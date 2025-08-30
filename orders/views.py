from django.db import transaction
from rest_framework.generics import (
    CreateAPIView, ListCreateAPIView, RetrieveAPIView,
    RetrieveUpdateDestroyAPIView, ListAPIView
)
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response

from orders.services.invoice_service import create_internal_invoice
from products.models import Tax

from .models import Invoice, Order, OrderItem, Payment, ShippingAddress, Coupon
from .serializers import (
    CreateOrderSerializer, InvoiceDisplaySerializer,
    OrderItemSerializer, OrderSerializer, CouponSerializer,
    PaymentSerializer, ShippingAddressSerializer,
    VendorOrderSerializer, VendorPaymentSerializer,
    VendorInvoiceSerializer,
)
from .services.payments.resolver import PaymentGatewayResolver

from products.permissions import IsVendor
from products.pagination import CustomPagination
from django.db.models import Prefetch
from django.utils.timezone import now
from django.conf import settings
from .tasks import send_order_email_async

# -------- Shipping Addresses --------
class ShippingAddressListCreate(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ShippingAddressSerializer

    def get_queryset(self):
        return (ShippingAddress.objects.filter(user=self.request.user)
                .order_by('-is_default', '-created_at'))

class ShippingAddressDetail(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ShippingAddressSerializer
    
    def get_queryset(self):
        return ShippingAddress.objects.filter(user=self.request.user)
    
    def perform_destroy(self, instance):
        user = instance.user
        was_default = instance.is_default
        super().perform_destroy(instance)
        if was_default:
            with transaction.atomic():
                candidate = (ShippingAddress.objects
                            .select_for_update(skip_locked=True)
                            .filter(user=user)
                            .order_by('-created_at')
                            .first())
                if candidate and not candidate.is_default:
                    candidate.is_default = True
                    candidate.save(update_fields=['is_default'])

# -------- Coupons --------
class CouponListView(ListAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAdminUser]

class CouponDetailView(RetrieveAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAdminUser]
    
class PublicCouponListView(ListAPIView):
    serializer_class = CouponSerializer

    def get_queryset(self):
        return Coupon.objects.filter(is_active=True, is_public=True)

# -------- Orders --------
class OrderListView(ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return (Order.objects
                .filter(user=self.request.user)
                .select_related('shipping_address', 'payment', 'user')
                .prefetch_related('items', 'items__variant', 'items__variant__product'))
   
class OrderCreateView(CreateAPIView):
    serializer_class = CreateOrderSerializer
    permission_classes = [IsAuthenticated]
    
class OrderDetailView(RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return (Order.objects
                .filter(user=self.request.user)
                .select_related('shipping_address', 'payment', 'user')
                .prefetch_related('items', 'items__variant', 'items__variant__product'))

class OrderItemListView(ListAPIView):
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        order_id = self.kwargs['order_id']
        return (OrderItem.objects
                .filter(order__id=order_id, order__user=self.request.user)
                .select_related('variant', 'variant__product'))

# -------- Payments --------
class PaymentDetailView(RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user)
               
class PaymentCallbackView(APIView):
    permission_classes = [AllowAny]
    
    def _process_result(self, result):
        if not result:
            return Response({"detail": "Unhandled or invalid event"}, status=400)
        transaction_id = result.get("transaction_id")
        status = result.get("status")
        order_id = result.get("order_id")
        
        # Find payment by transaction_id OR order_id
        payment = Payment.objects.filter(transaction_id=transaction_id).select_related("order").first()
        if not payment:
            payment = Payment.objects.filter(gateway_order_id=order_id).select_related("order").first()

        if not payment:
            return Response({"detail": "Payment not found."}, status=404)

        # Update payment once
        payment.transaction_id = transaction_id
        payment.status = status
        payment.save(update_fields=["transaction_id", "status"])

        order = payment.order
        # Only handle stock + invoice if successful
        if status == "success" and not hasattr(order, "invoice"):
            with transaction.atomic():
                items = order.items.select_for_update().select_related('variant')
                for item in items:
                    variant = item.variant
                    if variant.stock < item.quantity:
                        raise ValueError(f"Not enough stock for {variant.sku}")
                    variant.stock -= item.quantity
                    variant.save(update_fields=['stock'])

                create_internal_invoice(order, status='issued')

                order.status = 'paid'
                order.save(update_fields=['status'])
                
                context = {
                    "customer_name": order.user.first_name or order.user.username,
                    "customer_email": order.user.email,
                    "vendor_name": order.items.first().vendor.vendor_profile.store_name if order.items.exists() else "Vendor",
                    "vendor_email": order.items.first().vendor.email if order.items.exists() else settings.DEFAULT_FROM_EMAIL,
                    "order_id": order_id,
                    "current_year": now().year,
                }
                send_order_email_async.delay("Order Confirmation", "orders/order_created.html", context)
                    
        return Response(result)
    
    def post(self, request, gateway_type):
        gateway = PaymentGatewayResolver.resolve(gateway_type)
        result = gateway.callback(request)
        self._process_result(result)
        return Response(result)
    
    def get(self, request, gateway_type):
        gateway = PaymentGatewayResolver.resolve(gateway_type)
        result = gateway.callback_query(request.query_params)
        self._process_result(result)
        return Response(result)

# -------- Invoices --------
class InvoiceListView(ListAPIView):
    serializer_class = InvoiceDisplaySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return (Invoice.objects
                .filter(order__user=self.request.user)
                .select_related('order')
                .prefetch_related('order__user', 'order__items',
                                  'order__items__variant',
                                  'order__items__variant__product')
                )
  
class InvoiceDetailView(RetrieveAPIView):
    serializer_class = InvoiceDisplaySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return (Invoice.objects
                .filter(order__user=self.request.user)
                .select_related('order')
                .prefetch_related('order__user', 'order__items',
                                  'order__items__variant',
                                  'order__items__variant__product')
                )


# ---------VENDOR -----------
# Orders
class VendorOrderListView(ListAPIView):
    serializer_class = VendorOrderSerializer
    permission_classes = [IsVendor]
    pagination_class = CustomPagination

    def get_queryset(self):
        vendor = self.request.user
        
        vendor_items = OrderItem.objects.filter(vendor=vendor).select_related(
                "variant",
                "variant__product",
                "vendor"
            )
                
        return (
            Order.objects.filter(items__vendor=vendor)
            .select_related("user", "shipping_address") 
            .prefetch_related(Prefetch("items", queryset=vendor_items, to_attr="vendor_items"))
            .distinct()
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        context["active_taxes"] = list(Tax.objects.filter(is_active=True))
        return context

class VendorOrderDetailView(RetrieveAPIView):
    serializer_class = VendorOrderSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        vendor = self.request.user
        vendor_items = OrderItem.objects.filter(vendor=vendor).select_related(
                "variant",
                "variant__product",
                "vendor"
            )
        return (
            Order.objects.filter(items__vendor=vendor)
            .select_related("user", "shipping_address") 
            .prefetch_related(Prefetch("items", queryset=vendor_items, to_attr="vendor_items"))
            .distinct()
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        context["active_taxes"] = list(Tax.objects.filter(is_active=True))
        return context

# Payments
class VendorPaymentListView(ListAPIView):
    serializer_class = VendorPaymentSerializer
    permission_classes = [IsVendor]
    pagination_class = CustomPagination

    def get_queryset(self):
        vendor = self.request.user
        vendor_items = (
            OrderItem.objects.filter(vendor=vendor)
            .select_related("variant", "variant__product", "vendor")
        )
        return (
            Payment.objects.filter(order__items__vendor=vendor)
            .select_related("order")
            .prefetch_related(
                Prefetch("order__items", queryset=vendor_items, to_attr="vendor_items")
            )
            .distinct()
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        context["active_taxes"] = list(Tax.objects.filter(is_active=True))
        return context

class VendorPaymentDetailView(RetrieveAPIView):
    serializer_class = VendorPaymentSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        vendor = self.request.user
        vendor_items = (
            OrderItem.objects.filter(vendor=vendor)
            .select_related("variant", "variant__product", "vendor")
        )
        return (
            Payment.objects.filter(order__items__vendor=vendor)
            .select_related("order")
            .prefetch_related(
                Prefetch("order__items", queryset=vendor_items, to_attr="vendor_items")
            )
            .distinct()
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        context["active_taxes"] = list(Tax.objects.filter(is_active=True))
        return context

# Invoices
class VendorInvoiceListView(ListAPIView):
    serializer_class = VendorInvoiceSerializer
    permission_classes = [IsVendor]
    pagination_class = CustomPagination

    def get_queryset(self):
        vendor = self.request.user
        vendor_items = (
            OrderItem.objects.filter(vendor=vendor)
            .select_related("variant", "variant__product", "vendor")
        )
        return (
            Invoice.objects.filter(order__items__vendor=vendor)
            .select_related('order')
            .prefetch_related(
                Prefetch("order__items", queryset=vendor_items, to_attr="vendor_items")
            )
            .distinct()
            .order_by('-issued_at')
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        context["active_taxes"] = list(Tax.objects.filter(is_active=True))
        return context

class VendorInvoiceDetailView(RetrieveAPIView):
    serializer_class = VendorInvoiceSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        vendor = self.request.user
        vendor_items = (
            OrderItem.objects.filter(vendor=vendor)
            .select_related("variant", "variant__product", "vendor")
        )
        return (
            Invoice.objects.filter(order__items__vendor=vendor)
            .select_related('order')
            .prefetch_related(
                Prefetch("order__items", queryset=vendor_items, to_attr="vendor_items")
            )
            .distinct()
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        context["active_taxes"] = list(Tax.objects.filter(is_active=True))
        return context
