import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.text import slugify
from django.db.models import Q, ForeignKey
from django.conf import settings
from django.core.exceptions import ValidationError
from backend.utils import (
    HashedUploadPath,
    validate_image_extension,
    validate_image_size
)
class Category(models.Model):
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='children',
        null=True,
        blank=True,
        help_text="Leave blank for top-level categories."
    )
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
        help_text="Vendor who owns this category."
    )
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        
    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        self.name = self.name.strip().title()
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

class Brand(models.Model):
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="brands",
        help_text="Vendor who owns this brand."
    )
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        self.name = self.name.strip().title()
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

class Product(models.Model):
    class ConditionStatus(models.TextChoices):
        NEW = "new", "New"
        USED = "used", "Used"
        REFURBISHED = "refurbished", "Refurbished"
        
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
        help_text="Vendor who owns this product."
    )
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    warranty_years = models.PositiveSmallIntegerField(blank=True, null=True)
    condition = models.CharField(
        max_length=20,
        choices=ConditionStatus.choices
    )
    is_featured = models.BooleanField(default=False)
    is_weekly_deal = models.BooleanField(default=False)
    weekly_deal_expires = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.brand} {self.name}"
    
    def save(self, *args, **kwargs):
        self.name = self.name.strip().title()
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
        return super().save(*args, **kwargs)

class Specification(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name}"

class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specs')
    specification = models.ForeignKey(Specification, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('product', 'specification')
    
    def __str__(self):
        return f"{self.product}: {self.specification.name} = {self.value}"
    
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['product'],
                condition=Q(is_default=True),
                name='unique_default_variant_per_product'
            )
        ]
        
    def __str__(self):
        return f"{self.product.name} - {self.sku}"
    
    def clean(self):
        # Price must be non-negative
        if self.price is not None and self.price < Decimal('0'):
            raise ValidationError({"price": "Price cannot be negative."})
        # Discounted price checks
        if self.discounted_price is not None:
            if self.discounted_price < Decimal('0'):
                raise ValidationError({"discounted_price": "Discounted price cannot be negative."})
            if self.discounted_price > self.price:
                raise ValidationError({"discounted_price": "Discounted price cannot exceed the main price."})
            
        # First variant must be default — only if product already exists
        if not self.pk and self.product_id:
            if not self.product.variants.exists() and not self.is_default:
                raise ValidationError({"is_default": "The first variant for a product must be marked as default."})
            
    def save(self, *args, **kwargs):
        if not self.sku:
            brand_part = slugify(str(self.product.brand))[:6] or "brand"
            name_part = slugify(self.product.name)[:6] or "prod"
            self.sku = f"{brand_part}-{name_part}-{uuid.uuid4().hex[:6]}"
        self.full_clean()
        return super().save(*args, **kwargs)

class VariantSpecification(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='specs')
    specification = models.ForeignKey(Specification, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('variant', 'specification')

    def __str__(self):
        return f"{self.variant}: {self.specification.name} = {self.value}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    url = models.ImageField(
        upload_to=HashedUploadPath("products/"),
        validators=[validate_image_extension, validate_image_size]
    )
    alt_text = models.CharField(max_length=255, blank=True, null=True, help_text="Alternative text for accessibility/SEO.")
    caption = models.CharField(max_length=255, blank=True, null=True, help_text="Short caption or description of the image.")
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_primary']
        
    def __str__(self):
        return f"{self.url}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.variant and self.product and self.variant.product_id != self.product_id:
            raise ValidationError({"variant": "Selected variant must belong to the chosen product."})


class ProductReview(models.Model):
    class Rating(models.IntegerChoices):
        ONE = 1, "1"
        TWO = 2, "2"
        THREE = 3, "3"
        FOUR = 4, "4"
        FIVE = 5, "5"
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', db_index=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='replies', null=True, blank=True)
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=Rating.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'],
                condition=Q(parent__isnull=True),
                name='unique_review_per_user_product'
            ),
            models.CheckConstraint(
                check=Q(rating__isnull=True) | Q(rating__gte=1, rating__lte=5),
                name='rating_range'
            )
        ]
        
        indexes = [
            # Speeds up listing top-level reviews
            models.Index(fields=['product', '-created_at', '-id']),
            # Speeds up listing replies to a review
            models.Index(fields=['parent', 'created_at', 'id']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.product}"


class Tax(models.Model):
    class TaxType(models.TextChoices):
        PERCENTAGE = "percentage", "Percentage"
        FIXED = "fixed", "Fixed"
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TaxType.choices)
    value = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "tax"
        verbose_name_plural = "taxes"
    
    def __str__(self):
        return f"{self.name} ({self.value}{'%' if self.type == 'percentage' else ''})"
    
    def clean(self):
        if self.type == self.TaxType.PERCENTAGE and not (0 <= self.value <= 100):
            raise ValidationError("Percentage tax must be between 0 and 100.")
        if self.type == self.TaxType.FIXED and self.value <= 0:
            raise ValidationError("Fixed tax must be greater than 0.")
        
    
    def calculate_tax(self, value):
        tax_amount = Decimal('0')
        if self.type == self.TaxType.PERCENTAGE:
            tax_amount += (value * self.value / 100)
        elif self.type == self.TaxType.FIXED:
            tax_amount += self.value
        return tax_amount
    
    def save(self, *args, **kwargs):
        self.name = self.name.strip().title()
        super().save(*args, **kwargs)
