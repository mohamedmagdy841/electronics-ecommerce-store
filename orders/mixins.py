from products.models import Tax

class VendorOrderTotalsMixin:
    def _vendor_items(self, order):
        vendor = self.context["request"].user
        return order.items.filter(vendor=vendor)

    def calculate_vendor_subtotal(self, order):
        return sum(item.unit_price * item.quantity for item in self._vendor_items(order))

    def calculate_vendor_discount(self, order):
        return sum(getattr(item, "discount_amount", 0) for item in self._vendor_items(order))

    def calculate_vendor_tax(self, order):
        subtotal = self.calculate_vendor_subtotal(order)
        discount = self.calculate_vendor_discount(order)
        taxable_amount = subtotal - discount
        tax_amount = 0
        for tax in Tax.objects.filter(is_active=True):
            tax_amount += tax.calculate_tax(taxable_amount)
        return tax_amount

    def calculate_vendor_total(self, order):
        return (
            self.calculate_vendor_subtotal(order)
            - self.calculate_vendor_discount(order)
            + self.calculate_vendor_tax(order)
        )
