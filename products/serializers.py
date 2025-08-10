from rest_framework import serializers
from .models import Category, Brand, Product, ProductVariant, Specification, ProductSpecification, ProductImage, VariantSpecification

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
        fields = ['specification', 'value']

        
class VariantSpecificationSerializer(serializers.ModelSerializer):
    specification = serializers.StringRelatedField()

    class Meta:
        model = VariantSpecification
        fields = ['specification', 'value']

class ProductDetailVariantSerializer(serializers.ModelSerializer):
    specs = VariantSpecificationSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            'sku',
            'price',
            'discounted_price',
            'stock',
            'is_default',
            'specs',
            'images'
        ]
     
class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageSerializer(source='primary_images', many=True, read_only=True)
    specs = ProductSpecificationSerializer(many=True, read_only=True)
    variants = ProductDetailVariantSerializer(many=True, read_only=True)
    
    price_range = serializers.SerializerMethodField()
    selected_variant = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'category', 'brand',
            'name', 'slug', 'description',
            'warranty_years', 'condition',
            'is_featured',
            'images', 'specs',
            'variants',
            'price_range','selected_variant',
            'created_at'
        ]
    
    def get_price_range(self, obj):
        vs = list(obj.variants.all())
        if not vs:
            return None
        prices = [(v.discounted_price or v.price) for v in vs]
        return {
            'min': str(min(prices)),
            'max': str(max(prices))
        }
        
    def get_selected_variant(self, obj):
        variant_param = self.context.get('variant_param')
        if not variant_param:
            return None
        variants = list(obj.variants.all())
        variant = next((v for v in variants if v.sku == variant_param or str(v.id) == variant_param), None)
        return ProductDetailVariantSerializer(variant).data if variant else None

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['price', 'discounted_price']

# Product List Serializer
class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(source='primary_images', many=True, read_only=True)
    default_variant = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'description', 'images', 'default_variant'
        ]
        
    def get_default_variant(self, obj):
        variants = list(obj.variants.all())
        variant = next((v for v in variants if v.is_default), None) or (variants[0] if variants else None)
        if variant:
            return ProductVariantSerializer(variant).data
        return None


