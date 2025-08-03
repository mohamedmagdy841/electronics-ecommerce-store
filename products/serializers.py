from rest_framework import serializers
from .models import Category, Brand, Product, Specification, ProductSpecification, ProductImage

class CategorySerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(read_only=True)
    children = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Category
        fields = ['name', 'slug', 'parent', 'children']

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['name', 'slug', 'created_at']

class SpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specification
        fields = ['name', 'created_at']

class ProductImageSerializer(serializers.ModelSerializer):
    url = serializers.ImageField(use_url=True)
    class Meta:
        model = ProductImage
        fields = ['url', 'alt_text', 'caption', 'is_primary']

class ProductSpecificationSerializer(serializers.ModelSerializer):
    specification = serializers.StringRelatedField()
    
    class Meta:
        model = ProductSpecification
        fields = ['specification', 'value', 'created_at']
        
class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    specs = ProductSpecificationSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'category', 'brand',
            'name', 'slug', 'description',
            'price', 'discounted_price', 'sku',
            'warranty_years', 'condition',
            'is_featured',
            'images', 'specs',
            'created_at'
        ]

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'description', 'price',
            'discounted_price', 'images'
        ]
