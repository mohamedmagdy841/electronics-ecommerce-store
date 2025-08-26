from django.db import transaction
from rest_framework.generics import (
    CreateAPIView, ListCreateAPIView, RetrieveAPIView,
    RetrieveUpdateDestroyAPIView, ListAPIView
)
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response

from orders.services.invoice_service import create_internal_invoice

from .models import Invoice, Order, OrderItem, Payment, ShippingAddress, Coupon
from .serializers import (
    CreateOrderSerializer, InvoiceDisplaySerializer,
    OrderItemSerializer, OrderSerializer, CouponSerializer,
    PaymentSerializer, ShippingAddressSerializer,
    VendorOrderSerializer, VendorPaymentSerializer,
)
from .services.payments.resolver import PaymentGatewayResolver

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiTypes,
)
from products.permissions import IsVendor

# -------- Shipping Addresses --------
@extend_schema_view(
    get=extend_schema(
        tags=["Shipping Addresses"],
        summary="List my shipping addresses",
        description="Get all saved shipping addresses for the authenticated user.",
        responses=ShippingAddressSerializer,
    ),
    post=extend_schema(
        tags=["Shipping Addresses"],
        summary="Create new shipping address",
        description="Add a new shipping address for the authenticated user.",
        request=ShippingAddressSerializer,
        responses={201: ShippingAddressSerializer},
    ),
)
class ShippingAddressListCreate(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ShippingAddressSerializer

    def get_queryset(self):
        return (ShippingAddress.objects.filter(user=self.request.user)
                .order_by('-is_default', '-created_at'))

@extend_schema_view(
    get=extend_schema(
        tags=["Shipping Addresses"],
        summary="Retrieve shipping address",
        parameters=[OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH)],
        responses=ShippingAddressSerializer,
    ),
    put=extend_schema(
        tags=["Shipping Addresses"],
        summary="Update shipping address",
        request=ShippingAddressSerializer,
        responses=ShippingAddressSerializer,
    ),
    delete=extend_schema(
        tags=["Shipping Addresses"],
        summary="Delete shipping address",
        responses={204: OpenApiResponse(description="Deleted")},
    ),
)
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
@extend_schema_view(
    get=extend_schema(
        tags=["Coupons"],
        summary="List coupons (Admin only)",
        responses=CouponSerializer,
    ),
    post=extend_schema(
        tags=["Coupons"],
        summary="Create coupon (Admin only)",
        request=CouponSerializer,
        responses={201: CouponSerializer},
    ),
)
class CouponListCreateView(ListCreateAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAdminUser]

@extend_schema_view(
    get=extend_schema(
        tags=["Coupons"],
        summary="Retrieve coupon (Admin only)",
        parameters=[OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH)],
        responses=CouponSerializer,
    ),
    put=extend_schema(
        tags=["Coupons"],
        summary="Update coupon (Admin only)",
        request=CouponSerializer,
        responses=CouponSerializer,
    ),
    delete=extend_schema(
        tags=["Coupons"],
        summary="Delete coupon (Admin only)",
        responses={204: OpenApiResponse(description="Deleted")},
    ),
)
class CouponDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAdminUser]

@extend_schema(
    tags=["Coupons"],
    summary="Public list of active coupons",
    description="Returns only coupons that are active and public.",
    responses=CouponSerializer,
)
class PublicCouponListView(ListAPIView):
    serializer_class = CouponSerializer

    def get_queryset(self):
        return Coupon.objects.filter(is_active=True, is_public=True)

# -------- Orders --------
@extend_schema(
    tags=["Orders"],
    summary="List my orders",
    description="Get all orders belonging to the authenticated user.",
    responses=OrderSerializer,
)
class OrderListView(ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return (Order.objects
                .filter(user=self.request.user)
                .select_related('shipping_address', 'payment', 'user')
                .prefetch_related('items', 'items__variant', 'items__variant__product'))

@extend_schema(
    tags=["Orders"],
    summary="Create order",
    description="Create a new order with cart items, shipping address, and optional coupon.",
    request=CreateOrderSerializer,
    responses={201: OrderSerializer},
)    
class OrderCreateView(CreateAPIView):
    serializer_class = CreateOrderSerializer
    permission_classes = [IsAuthenticated]
    
@extend_schema(
    tags=["Orders"],
    summary="Retrieve order details",
    parameters=[OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH)],
    responses=OrderSerializer,
)  
class OrderDetailView(RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return (Order.objects
                .filter(user=self.request.user)
                .select_related('shipping_address', 'payment', 'user')
                .prefetch_related('items', 'items__variant', 'items__variant__product'))

@extend_schema(
    tags=["Orders"],
    summary="List items for a specific order",
    parameters=[OpenApiParameter("order_id", OpenApiTypes.INT, OpenApiParameter.PATH)],
    responses=OrderItemSerializer,
)
class OrderItemListView(ListAPIView):
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        order_id = self.kwargs['order_id']
        return (OrderItem.objects
                .filter(order__id=order_id, order__user=self.request.user)
                .select_related('variant', 'variant__product'))

# -------- Payments --------
@extend_schema(
    tags=["Payments"],
    summary="Retrieve payment details",
    parameters=[OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH)],
    responses=PaymentSerializer,
)
class PaymentDetailView(RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user)

@extend_schema_view(
    post=extend_schema(
        tags=["Payments"],
        summary="Payment gateway callback (POST)",
        description="Handle async callback from payment gateway (e.g. Stripe, PayPal, Paymob).",
        request=OpenApiTypes.OBJECT,
        parameters=[
            OpenApiParameter(
                "gateway_type", OpenApiTypes.STR, OpenApiParameter.PATH,
                description="Payment gateway type (stripe/paypal/paymob/...)"
            ),
        ],
        responses={
            200: OpenApiResponse(description="Processed successfully"),
            400: OpenApiResponse(description="Invalid event or unhandled"),
            404: OpenApiResponse(description="Payment not found"),
        },
    ),
    get=extend_schema(
        tags=["Payments"],
        summary="Payment gateway callback (GET query)",
        description="Handle redirect/callback with query parameters from gateway.",
        parameters=[
            OpenApiParameter(
                "gateway_type", OpenApiTypes.STR, OpenApiParameter.PATH,
                description="Payment gateway type (stripe/paypal/paymob/...)"
            ),
        ],
        responses={
            200: OpenApiResponse(description="Processed successfully"),
            400: OpenApiResponse(description="Invalid event or unhandled"),
            404: OpenApiResponse(description="Payment not found"),
        },
    ),
)                  
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
@extend_schema(
    tags=["Invoices"],
    summary="List my invoices",
    responses=InvoiceDisplaySerializer,
)
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

@extend_schema(
    tags=["Invoices"],
    summary="Retrieve invoice",
    parameters=[OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH)],
    responses=InvoiceDisplaySerializer,
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

    def get_queryset(self):
        vendor = self.request.user
        return (
            Order.objects.filter(items__vendor=vendor)
            .distinct()
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

class VendorOrderDetailView(RetrieveAPIView):
    serializer_class = VendorOrderSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        vendor = self.request.user
        return Order.objects.filter(items__vendor=vendor).distinct()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

# Payments
class VendorPaymentListView(ListAPIView):
    serializer_class = VendorPaymentSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        vendor = self.request.user
        return (
            Payment.objects.filter(order__items__vendor=vendor)
            .distinct()
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class VendorPaymentDetailView(RetrieveAPIView):
    serializer_class = VendorPaymentSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        vendor = self.request.user
        return Payment.objects.filter(order__items__vendor=vendor).distinct()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
