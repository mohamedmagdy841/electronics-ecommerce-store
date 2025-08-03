from django.contrib import admin
from .models import (
    Category, Brand, Product, Specification,
    ProductSpecification, ProductImage
)
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin

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
        'id', 'name', 'brand', 'category', 'price',
        'is_featured', 'is_weekly_deal', 'condition', 'created_at'
    ]
    list_filter = ['category', 'brand', 'is_featured', 'condition']
    search_fields = ['name', 'sku', 'slug']
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, ProductSpecificationInline]
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
