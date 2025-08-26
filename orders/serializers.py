from decimal import Decimal
from rest_framework import serializers
from cart.models import CartItem
from products.models import Tax
from .services.order_service import create_order
from .models import ShippingAddress, Coupon, Order, OrderItem, Payment, Invoice
from accounts.serializers import CustomUserSerializer

class ShippingAddressSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)
    
    class Meta:
        model = ShippingAddress
        fields = [
            "id", "full_name", "phone_number",
            "address_line_1", "address_line_2",
            "city", "state", "postal_code", "country", "country_name",
            "instructions", "is_default"
        ]
        read_only_fields = ["id"]
        
    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["user"] = user

        if not ShippingAddress.objects.filter(user=user).exists():
            validated_data["is_default"] = True

        if validated_data.get("is_default") is True:
            ShippingAddress.objects.filter(user=user).update(is_default=False)
            
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get('is_default') is True:
            (ShippingAddress.objects
             .filter(user=instance.user)
             .exclude(pk=instance.pk)
             .update(is_default=False))
            
        return super().update(instance, validated_data)

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = "__all__"

    def validate(self, attrs):
        if (
            attrs.get("discount_type") == Coupon.DiscountType.PERCENT
            and attrs.get("value") is not None
            and attrs["value"] > 100
        ):
            raise serializers.ValidationError(
                {"value": "Percent value cannot exceed 100."}
            )
        return attrs
    
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='variant.product.name', read_only=True)
    sku = serializers.CharField(source='variant.sku', read_only=True)
    total_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = ['id', 'variant', 'product_name', 'sku', 'quantity', 'unit_price', 'total_price']
        read_only_fields = ['unit_price', 'total_price', 'product_name', 'sku']

class PaymentSerializer(serializers.ModelSerializer):
    is_paid = serializers.BooleanField(read_only=True)
    method = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = ['id', 'method', 'amount', 'status', 'transaction_id', 'is_paid', 'created_at']
        read_only_fields = ['status', 'transaction_id', 'is_paid', 'created_at']
        
    def get_method(self, obj):
        return obj.get_method_display().upper()

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)
    shipping_address = ShippingAddressSerializer(read_only=True)
    user = CustomUserSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    grand_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'shipping_address', 'status',
            'subtotal', 'discount_amount', 'total_tax', 'grand_total',
            'total_price', 'coupon_code', 'created_at',
            'items', 'payment'
        ]
        read_only_fields = ['status', 'subtotal', 'grand_total', 'total_price', 'created_at']

class CreateOrderSerializer(serializers.ModelSerializer):
    shipping_address = serializers.PrimaryKeyRelatedField(queryset=ShippingAddress.objects.all())
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Order
        fields = ['shipping_address', 'coupon_code', 'payment_method']

    def validate(self, attrs):
        user = self.context['request'].user

        cart_items = CartItem.objects.filter(cart__user=user)
        if not cart_items.exists():
            raise serializers.ValidationError("Your cart is empty.")

        return attrs

    def create(self, validated_data):
        order, payment_data = create_order(
            user=self.context['request'].user,
            shipping_address=validated_data['shipping_address'],
            coupon_code=validated_data.get('coupon_code'),
            payment_method=validated_data.get('payment_method')
        )

        self.context['payment_data'] = payment_data
        return order
    
    def to_representation(self, instance):
        order_data = OrderSerializer(instance, context=self.context).data
        payment_data = self.context.get('payment_data')
        if payment_data:
            order_data['payment_action'] = payment_data
        return order_data

class InvoiceDisplaySerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source="order.id", read_only=True)
    user = serializers.CharField(source="order.user.email", read_only=True)
    items = OrderItemSerializer(source="order.items", many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "status",
            "order_id",
            "user",
            "billing_address",
            "issued_at",
            "due_date",
            "subtotal",
            "discount",
            "tax",
            "total",
            "items",
        ]

# ---------- VENDOR ----------
# Order
class VendorOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="variant.product.name", read_only=True)
    sku = serializers.CharField(source="variant.sku", read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "order",
            "sku",
            "product_name",
            "quantity",
            "unit_price",
            "total_price",
        ]

class VendorOrderSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    vendor_subtotal = serializers.SerializerMethodField()
    vendor_discount_amount = serializers.SerializerMethodField()
    vendor_tax = serializers.SerializerMethodField()
    vendor_total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "shipping_address",
            "status",
            "coupon_code",
            "created_at",
            "vendor_subtotal",
            "vendor_discount_amount",
            "vendor_tax",
            "vendor_total",
            "items",
        ]

    def get_items(self, obj):
        vendor = self.context["request"].user
        qs = obj.items.filter(vendor=vendor)
        return VendorOrderItemSerializer(qs, many=True).data

    def get_vendor_subtotal(self, obj):
        vendor = self.context["request"].user
        qs = obj.items.filter(vendor=vendor)
        return sum(item.unit_price * item.quantity for item in qs)

    def get_vendor_discount_amount(self, obj):
        vendor_subtotal = self.get_vendor_subtotal(obj)

        order_subtotal = obj.subtotal
        if order_subtotal == 0 or obj.discount_amount == 0:
            return 0

        return (vendor_subtotal / order_subtotal) * obj.discount_amount

    def get_vendor_tax(self, obj):
        vendor_subtotal = self.get_vendor_subtotal(obj)
        vendor_discount = self.get_vendor_discount_amount(obj)

        taxable_amount = vendor_subtotal - vendor_discount
        tax_amount = Decimal("0")

        for tax in Tax.objects.filter(is_active=True):
            tax_amount += tax.calculate_tax(taxable_amount)

        return tax_amount

    def get_vendor_total(self, obj):
        vendor_subtotal = self.get_vendor_subtotal(obj)
        vendor_discount = self.get_vendor_discount_amount(obj)
        vendor_tax = self.get_vendor_tax(obj)
        return vendor_subtotal - vendor_discount + vendor_tax

# Payment

class VendorPaymentSerializer(serializers.ModelSerializer):
    order = serializers.SerializerMethodField()
    vendor_amount = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "method",
            "provider",
            "vendor_amount",
            "amount",
            "status",
            "gateway_order_id",
            "transaction_id",
            "created_at",
        ]

    def get_order(self, obj):
        return VendorOrderSerializer(obj.order, context=self.context).data
    
    def get_vendor_amount(self, obj):
        vendor_order = VendorOrderSerializer(obj.order, context=self.context)
        return vendor_order.data.get("vendor_total", 0)
