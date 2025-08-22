from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import (
    Category, Brand, Product, ProductVariant, Specification,
    ProductSpecification, ProductImage, Tax, VariantSpecification
)
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError

# ---- Inline for Product Images ----
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ['image_tag']

    def image_tag(self, obj):
        if obj.url:
            return format_html('<img src="{}" width="60" />', obj.url.url)
        return "-"
    image_tag.short_description = 'Image'

# ---- Inline for Product Specs ----
class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1

# ---- Formset for Product Variants ----
class ProductVariantInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        variants = [form.cleaned_data for form in self.forms if not form.cleaned_data.get('DELETE', False)]
        if variants:
            if not any(v.get('is_default') for v in variants):
                raise ValidationError("The first variant for a product must be marked as default.")
            
# ---- Inline for Product Variants ----
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    min_num = 1
    validate_min = True
    formset = ProductVariantInlineFormSet

# ---- Category ----
@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    list_display = ['id', 'name', 'slug', 'is_active', 'created_at']
    list_editable = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {"slug": ("name",)}
    ordering = ['name']

# ---- Brand ----
@admin.register(Brand)
class BrandAdmin(ImportExportModelAdmin):
    list_display = ['id', 'name', 'slug', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {"slug": ("name",)}
    ordering = ['name']

# ---- Product ----
@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    list_display = [
        'id', 'name', 'brand', 'category', 'is_featured',
        'is_weekly_deal', 'condition', 'created_at'
    ]
    list_filter = ['category', 'brand', 'is_featured', 'condition']
    search_fields = ['name', 'sku', 'slug']
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, ProductSpecificationInline, ProductVariantInline]
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    

# ---- Specification ----
@admin.register(Specification)
class SpecificationAdmin(ImportExportModelAdmin):
    list_display = ['id', 'name', 'created_at']
    search_fields = ['name']

# ---- Product Specification ----
@admin.register(ProductSpecification)
class ProductSpecificationAdmin(ImportExportModelAdmin):
    list_display = ['id', 'product', 'specification', 'value']
    search_fields = ['product__name', 'specification__name', 'value']
    list_filter = ['specification']

# ---- Product Image ----
@admin.register(ProductImage)
class ProductImageAdmin(ImportExportModelAdmin):
    list_display = ['id', 'product', 'url', 'is_primary', 'alt_text', 'caption']
    list_filter = ['is_primary']
    search_fields = ['product__name', 'alt_text', 'caption']
    readonly_fields = ['image_tag']
    def image_tag(self, obj):
        if obj.url:
            return format_html('<img src="{}" width="60" />', obj.url.url)
        return "-"
    image_tag.short_description = 'Image'
    
@admin.register(ProductVariant)
class ProductVariantAdmin(ImportExportModelAdmin):
    list_display = ['id', 'product', 'sku', 'price', 'discounted_price', 'stock', 'is_default', 'created_at']
    search_fields = ['product__name', 'sku']
    list_filter = ['product', 'is_default']
    readonly_fields = ['created_at', 'updated_at']
    
@admin.register(VariantSpecification)
class VariantSpecificationAdmin(ImportExportModelAdmin):
    list_display = ['id', 'variant', 'specification', 'value']
    search_fields = ['variant__product__name', 'specification__name', 'value']
    list_filter = ['specification']


# ---- Tax ----
@admin.register(Tax)
class TaxAdmin(ImportExportModelAdmin):
    list_display = ['id', 'name', 'value', 'type', 'is_active', 'created_at']
    search_fields = ['name']
    list_filter = ['type', 'is_active']
    readonly_fields = ['created_at', 'updated_at']

