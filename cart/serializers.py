from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from products.models import ProductVariant
from .models import Cart, CartItem, WishlistItem
from products.serializers import ProductImageSerializer

# Wishlist
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

# Cart
class CartVariantMiniSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='product.name', read_only=True)
    slug = serializers.SlugField(source='product.slug', read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = ["id", "sku", "name", "slug", "price", "discounted_price", "stock"]
        
class CartItemSerializer(serializers.ModelSerializer):
    variant = CartVariantMiniSerializer(read_only=True)
    line_total = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ["id", "variant", "quantity", "line_total", "created_at", "updated_at"]
    
    def get_line_total(self, obj):
        unit = obj.variant.discounted_price or obj.variant.price or Decimal("0")
        return str(unit * obj.quantity)

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cart_items', many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'items_count', 'subtotal']
        
    def get_items_count(self, obj):
        return sum(item.quantity for item in obj.cart_items.all())
    
    def get_subtotal(self, obj):
        total = Decimal("0")
        for item in obj.cart_items.select_related("variant"):
            unit = item.variant.discounted_price or item.variant.price or Decimal("0")
            total += unit * item.quantity
        return str(total)

class CartItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['variant']
    
    def validate_variant(self, value):
        if value is None:
            raise serializers.ValidationError("Variant is required.")
        return value
    
    def create(self, validated_data):
        cart = self.context['cart']
        variant = validated_data.get('variant')
        
        # to prevent race conditions
        with transaction.atomic():
            variant = ProductVariant.objects.select_for_update().get(pk=variant.pk)
            if variant.stock <= 0:
                raise serializers.ValidationError({"detail": "Out of stock."})
            
            item, created = CartItem.objects.select_for_update().get_or_create(
                cart=cart, variant=variant, defaults={'quantity': 1}
            )
            if not created:
                target = min(item.quantity + 1, variant.stock)
                
                if target == item.quantity:
                    return item
                
                CartItem.objects.filter(pk=item.pk).update(quantity=target)
                item.refresh_from_db()
        return item
    
