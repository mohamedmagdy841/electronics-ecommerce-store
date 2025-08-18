from django.db import transaction
from rest_framework.generics import CreateAPIView, ListCreateAPIView, RetrieveAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response

from orders.services.invoice_service import create_invoice

from .models import Invoice, Order, OrderItem, Payment, ShippingAddress, Coupon
from .serializers import CreateOrderSerializer, InvoiceDisplaySerializer, OrderItemSerializer, OrderSerializer, PaymentSerializer, ShippingAddressSerializer, CouponSerializer
from .services.payments.resolver import PaymentGatewayResolver

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
class CouponListCreateView(ListCreateAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAdminUser]

class CouponDetailView(RetrieveUpdateDestroyAPIView):
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
    
class PaymentDetailView(RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user)
                        
class PaymentCallbackView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, gateway_type):
        gateway = PaymentGatewayResolver.resolve(gateway_type)
        result = gateway.callback(request)

        transaction_id = result.get("transaction_id")
        status = result.get("status")

        try:
            payment = Payment.objects.select_related("order").get(transaction_id=transaction_id)
        except Payment.DoesNotExist:
            return Response({"detail": "Payment not found."}, status=404)

        payment.status = status
        payment.save(update_fields=["status"])

        if status == "success" and not hasattr(payment.order, "invoice"):
            create_invoice(payment.order, status="issued")
        return Response(result)


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
