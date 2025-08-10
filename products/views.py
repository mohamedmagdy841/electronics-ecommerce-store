from django.db.models import Prefetch
from rest_framework import generics
from django.utils import timezone
from .models import Brand, Product, Category, ProductImage, ProductVariant
from .serializers import (
    ProductSerializer,
    ProductDetailSerializer,
    CategorySerializer,
    BrandSerializer
)
from .pagination import CustomProductPagination
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ProductFilter
from rest_framework import filters

class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    pagination_class = CustomProductPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'brand__name', 'category__name', 'sku']
    ordering_fields = ['price', 'created_at']
    
    def get_queryset(self):
        return Product.objects.select_related(
            'category', 'brand'
        ).prefetch_related(
            'images', 'specs__specification', 'category__children', 
            Prefetch('variants', queryset=ProductVariant.objects.order_by('-is_default', 'id'))
        )

class ProductDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Product.objects.select_related(
            'category', 'brand'
        ).prefetch_related(
            'specs__specification', 'category__children',
            Prefetch(
                'images',
                queryset=(
                    ProductImage.objects
                    .filter(variant__isnull=True)
                    .order_by('-is_primary')
                ),
                to_attr='primary_images'
            ),
            Prefetch(
                'variants',
                queryset=(
                    ProductVariant.objects
                    .prefetch_related('specs__specification', 'images')
                    .order_by('-is_default', 'id')
                )
            ),
        )
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['variant_param'] = self.request.query_params.get('variant')
        return context

class SubcategoryListByCategoryAPIView(generics.ListAPIView):
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        parent_slug = self.kwargs['slug']
        return Category.objects.filter(parent__slug=parent_slug)
         

# Home Page Views
class LatestProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        products = cache.get("latest_products")
        
        if products is None:
            products = Product.objects.prefetch_related('images').order_by('-created_at')[:9]
            cache.set("latest_products", products, timeout=60*60)
            
        return products
    
class WeeklyDealProductAPIView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    
    def get_object(self):
        now = timezone.now()
        product = cache.get("weekly_deal_product")
        
        if product is None:
            product = (
                Product.objects
                .filter(is_weekly_deal=True,weekly_deal_expires__gte=now)
                .prefetch_related('images')
                .order_by('weekly_deal_expires')
                .first()
            )
            
            if not product:
                from rest_framework.exceptions import NotFound
                raise NotFound("No active weekly deal.")
            cache.set("weekly_deal_product", product, timeout=60*60)

        return product 
        
    ## Most Popular Products
    
class CategoryListAPIView(generics.ListAPIView):
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        categories = cache.get("category_list")
        
        if categories is None:
            categories = Category.objects.filter(parent__isnull=True, is_active=True).prefetch_related('children')[:9]
            cache.set("category_list", categories, timeout=60*60)

        return categories
    
class SubCategoryListAPIView(generics.ListAPIView):
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        categories = cache.get("subcategory_list")
        
        if categories is None:
            categories = Category.objects.filter(parent__isnull=False)[:9]
            cache.set("subcategory_list", categories, timeout=60*60)
            
        return categories 

class BrandListAPIView(generics.ListAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
