import uuid
from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='children',
        null=True,
        blank=True,
        help_text="Leave blank for top-level categories."
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
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sku = models.CharField(max_length=100, unique=True, db_index=True)
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


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    url = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=255, blank=True, null=True, help_text="Alternative text for accessibility/SEO.")
    caption = models.CharField(max_length=255, blank=True, null=True, help_text="Short caption or description of the image.")
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_primary']
        
    def __str__(self):
        return f"{self.url}"
