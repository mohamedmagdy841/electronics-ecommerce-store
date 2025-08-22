from orders.models import Invoice

def create_internal_invoice(order, status="draft"):
    next_number = f"INV-{Invoice.objects.count() + 1:06d}"
    return Invoice.objects.create(
        order=order,
        invoice_number=next_number,
        billing_address=str(order.shipping_address),
        subtotal=order.subtotal,
        discount=order.discount_amount,
        tax=order.total_tax,
        total=order.grand_total,
        status=status,
    )   
