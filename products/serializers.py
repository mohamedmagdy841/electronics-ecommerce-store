from rest_framework import serializers
from .models import (
    Category,
    Brand,
    Product,
    ProductVariant,
    Specification,
    ProductSpecification,
    ProductImage,
    VariantSpecification,
    ProductReview
)
from drf_spectacular.utils import extend_schema_field, inline_serializer, OpenApiTypes

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

# Product Detail Serializer
class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageSerializer(source='primary_images', many=True, read_only=True)
    specs = ProductSpecificationSerializer(many=True, read_only=True)
    variants = ProductDetailVariantSerializer(many=True, read_only=True)
    
    price_range = serializers.SerializerMethodField()
    selected_variant = serializers.SerializerMethodField()
    
    avg_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    rating_distribution = serializers.SerializerMethodField()
    
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
            'avg_rating', 'review_count', 'rating_distribution',
            'created_at'
        ]
    
    @extend_schema_field(dict)
    def get_price_range(self, obj):
        vs = list(obj.variants.all())
        if not vs:
            return None
        prices = [(v.discounted_price or v.price) for v in vs]
        return {
            'min': str(min(prices)),
            'max': str(max(prices))
        }
        
    @extend_schema_field(ProductDetailVariantSerializer)
    def get_selected_variant(self, obj):
        variant_param = self.context.get('variant_param')
        if not variant_param:
            return None
        variants = list(obj.variants.all())
        variant = next((v for v in variants if v.sku == variant_param or str(v.id) == variant_param), None)
        return ProductDetailVariantSerializer(variant, context=self.context).data if variant else None
    
    @extend_schema_field(list)
    def get_rating_distribution(self, obj):
        # Only if you added r1..r5 in the queryset
        if hasattr(obj, "r1"):
            return [obj.r1, obj.r2, obj.r3, obj.r4, obj.r5]
        return None

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
        
    @extend_schema_field(ProductVariantSerializer)
    def get_default_variant(self, obj):
        variants = list(obj.variants.all())
        variant = next((v for v in variants if v.is_default), None) or (variants[0] if variants else None)
        if variant:
            return ProductVariantSerializer(variant).data
        return None


class ReviewReplySerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    class Meta:
        model = ProductReview
        fields = ["id", "user", "content", "created_at"]

class ProductReviewSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    parent = serializers.PrimaryKeyRelatedField(
        queryset=ProductReview.objects.all(), required=False, allow_null=True
    )
    replies = ReviewReplySerializer(many=True, read_only=True)
    
    class Meta:
        model = ProductReview
        fields = ['id', 'user', 'content', 'rating', 'parent', 'created_at', 'replies']
        read_only_fields = ["id", "user", "created_at", "replies"]
    
    def validate(self, attrs):
        request = self.context["request"]
        product = self.context["product"]
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        
        # If replying
        if parent:
            # Prevents replying to a reply
            if parent.parent_id is not None:
                raise serializers.ValidationError("Replies are limited to one level.")

            # No replying to a review on another product
            if parent.product_id != product.id:
                raise serializers.ValidationError("Parent review belongs to a different product.")

            # Ratings are only for top-level reviews
            if attrs.get("rating") is not None:
                raise serializers.ValidationError("Replies cannot include a rating.")

        # If top-level
        else:
            # Rating is required for top-level reviews
            if attrs.get("rating") is None:
                raise serializers.ValidationError("Rating is required for a review.")

            qs = ProductReview.objects.filter(
                user=request.user,
                product=product,
                parent__isnull=True
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise serializers.ValidationError("You have already reviewed this product.")
        return attrs
    
    def create(self, validated_data):
        request = self.context.get('request')
        product = self.context.get('product')
        return ProductReview.objects.create(
            user=request.user,
            product=product,
            **validated_data
        )

# ----------Vendor----------

class VendorProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'category', 'brand', 'name', 'description',
            'warranty_years', 'condition', 'is_featured',
            'is_weekly_deal', 'weekly_deal_expires'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        request = self.context['request']
        validated_data['vendor'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('vendor', None)
        return super().update(instance, validated_data)

class VendorProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'price', 'discounted_price',
            'stock', 'is_default'
        ]
        read_only_fields = ['id', 'sku']
    
    def validate(self, attrs):
        product = self.context['product']
        is_default = attrs.get("is_default", False)

        if is_default:
            qs = product.variants.filter(is_default=True)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("This product already has a default variant.")
            
        return attrs
    
    def create(self, validated_data):
        product = self.context.get('product')
        return ProductVariant.objects.create(
            product=product,
            **validated_data
        )

class VendorProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "url", "alt_text", "caption", "is_primary", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        product = self.context["product"]
        variant = self.context.get("variant", None)
        return ProductImage.objects.create(product=product, variant=variant, **validated_data)

class VendorProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = ['id', 'product', 'specification', 'value']
        read_only_fields = ['id']

class VendorVariantSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantSpecification
        fields = ['id', 'variant', 'specification', 'value']
        read_only_fields = ['id']
