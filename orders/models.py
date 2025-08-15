from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django_countries.fields import CountryField
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class ShippingAddress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shipping_addresses"
    )
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20)
    country = CountryField()
    instructions = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Shipping Addresses"
        indexes = [
            models.Index(fields=["user", "is_default"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_default=True),
                name="unique_default_address_per_user",
            )
        ]

    def __str__(self):
        return f"{self.full_name}, {self.address_line_1}, {self.city}"

class Coupon(models.Model):
    class DiscountType(models.TextChoices):
        PERCENT = "percent", "Percent"
        FIXED = "fixed", "Fixed amount"

    code = models.CharField(max_length=40, unique=True)
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(
        default=False,
        help_text="If True and active, show on frontend."
    )
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    discount_type = models.CharField(max_length=10, choices=DiscountType.choices)
    value = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Percent: use 10 for 10%. Fixed: currency units."
    )
    max_uses = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Global cap across all orders. Null = unlimited."
    )
    min_order_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Apply only if order subtotal >= this amount."
    )
    first_order_only = models.BooleanField(
        default=False,
        help_text="Use for the one-time welcome coupon (only valid on a user's first order)."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="coupon_value_range_by_type",
                check=(
                    models.Q(discount_type="fixed", value__gte=0) |
                    models.Q(discount_type="percent", value__gte=0, value__lte=100)
                ),
            ),
        ]
        indexes = [
            models.Index(fields=["is_active", "is_public", "valid_from", "valid_to"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return self.code
    
    def clean(self):
        if self.discount_type == self.DiscountType.PERCENT and (self.value is not None) and self.value > 100:
            raise ValidationError({"value": _("Percent value cannot exceed 100.")})
        
    def is_in_time_window(self) -> bool:
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        return True
