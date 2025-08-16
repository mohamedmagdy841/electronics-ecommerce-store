from django.db import transaction
from decimal import Decimal
from cart.models import CartItem
from products.models import Tax
from ..models import Coupon, Order, OrderItem, Payment
import uuid

def create_order(user, shipping_address, coupon_code=None, payment_method='cod'):
    cart_items = CartItem.objects.filter(cart__user=user)
    if not cart_items.exists():
        raise ValueError("Cart is empty")

    subtotal = sum(
        (item.variant.discounted_price or item.variant.price) * item.quantity
        for item in cart_items
    )

    discount_amount = Decimal('0')
    if coupon_code:
        discount_amount = Coupon.validate_and_get_discount(coupon_code, user, subtotal)

    total_tax = sum(
        tax.calculate_tax(subtotal)
        for tax in Tax.objects.filter(is_active=True)
    )

    total_price = subtotal - discount_amount + total_tax

    with transaction.atomic():
        order = Order.objects.create(
            user=user,
            shipping_address=shipping_address,
            total_price=total_price,
            discount_amount=discount_amount,
            total_tax=total_tax,
            coupon_code=coupon_code
        )

        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                variant=item.variant,
                quantity=item.quantity,
                unit_price=item.variant.discounted_price or item.variant.price
            )
            for item in cart_items
        ])

        Payment.objects.create(
            order=order,
            method=payment_method,
            transaction_id=str(uuid.uuid4()),
            amount=total_price,
            status='pending'
        )
        
        if payment_method == 'cod':
            for item in cart_items:
                if item.variant.stock < item.quantity:
                    raise ValueError(f"Not enough stock for {item.variant.sku}")
                item.variant.stock -= item.quantity
                item.variant.save(update_fields=['stock'])

        cart_items.delete()

    return order
