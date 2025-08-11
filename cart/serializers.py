from rest_framework import serializers

from products.models import ProductVariant
from .models import WishlistItem
from products.serializers import ProductImageSerializer

class WishlistVariantSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='product.name', read_only=True)
    slug = serializers.SlugField(source='product.slug', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = ['id', 'sku', 'name', 'slug', 'price', 'discounted_price', 'stock', 'images']

class WishlistItemSerializer(serializers.ModelSerializer):
    variant = WishlistVariantSerializer(read_only=True)
    
    class Meta:
        model = WishlistItem
        fields = ['id', 'variant', 'created_at']

        
class WishlistCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishlistItem
        fields = ['variant']
