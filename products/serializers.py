from rest_framework import serializers
from .models import Category, Brand, Product, Specification, ProductSpecification, ProductImage

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'is_active', 'created_at', 'updated_at']

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'created_at', 'updated_at']

class SpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specification
        fields = ['id', 'name', 'created_at', 'updated_at']

class ProductImageSerializer(serializers.ModelSerializer):
    url = serializers.ImageField(use_url=True)
    class Meta:
        model = ProductImage
        fields = [
            'id', 'url', 'alt_text', 'caption', 'is_primary',
            'created_at', 'updated_at'
        ]

class ProductSpecificationSerializer(serializers.ModelSerializer):
    specification = serializers.StringRelatedField()
    
    class Meta:
        model = ProductSpecification
        fields = [
            'id', 'specification', 'value',
            'created_at', 'updated_at'
        ]
        
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    specs = ProductSpecificationSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'category', 'brand',
            'name', 'slug', 'description',
            'price', 'discounted_price', 'sku',
            'warranty_years', 'condition',
            'is_featured',
            'images', 'specs',
            'created_at', 'updated_at'
        ]
