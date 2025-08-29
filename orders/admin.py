from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import ShippingAddress, Coupon, Order, OrderItem, Payment, Invoice


@admin.register(ShippingAddress)
class ShippingAddressAdmin(ModelAdmin):
    list_display = ('user', 'full_name', 'phone_number', 'city', 'country', 'is_default')
    search_fields = ('full_name', 'phone_number', 'city', 'country')
    list_filter = ('country', 'is_default')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Coupon)
class CouponAdmin(ModelAdmin):
    list_display = ('code', 'discount_type', 'value', 'is_active', 'is_public', 'valid_from', 'valid_to')
    search_fields = ('code',)
    list_filter = ('discount_type', 'is_active', 'is_public', 'first_order_only')
    readonly_fields = ('created_at', 'updated_at')


# ---- INLINES ----
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price',)


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0
    max_num = 1
    readonly_fields = ('created_at',)


class InvoiceInline(admin.StackedInline):
    model = Invoice
    extra = 0
    max_num = 1
    readonly_fields = ('issued_at',)


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'discount_amount', 'total_tax', 'created_at')
    search_fields = ('user__email', 'user__username', 'id')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at',)
    inlines = [OrderItemInline, PaymentInline, InvoiceInline]


@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    list_display = ('order', 'variant', 'vendor', 'quantity', 'unit_price', 'total_price')
    search_fields = ('order__id', 'variant__product__name', 'vendor__email')
    list_filter = ('vendor',)


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ('order', 'method', 'provider', 'amount', 'status', 'created_at')
    search_fields = ('order__id', 'transaction_id', 'gateway_order_id')
    list_filter = ('status', 'method', 'provider')
    readonly_fields = ('created_at',)


@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = ('invoice_number', 'order', 'status', 'issued_at', 'due_date', 'total')
    search_fields = ('invoice_number', 'order__id')
    list_filter = ('status', 'issued_at')
    readonly_fields = ('issued_at',)
