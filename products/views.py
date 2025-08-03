from rest_framework import generics
from django.utils import timezone
from .models import Product, Category
from .serializers import (
    ProductSerializer,
    ProductDetailSerializer,
    CategorySerializer,
)
from .pagination import CustomProductPagination

class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    pagination_class = CustomProductPagination
    
    def get_queryset(self):
        return Product.objects.select_related(
            'category', 'brand'
        ).prefetch_related(
            'images', 'specs__specification', 'category__children'
        )

class ProductDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Product.objects.select_related(
            'category', 'brand'
        ).prefetch_related(
            'images', 'specs__specification', 'category__children'
        )

# Home Page Views
class LatestProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        return Product.objects.prefetch_related('images').order_by('-created_at')[:9]
    
class WeeklyDealProductAPIView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    
    def get_object(self):
        now = timezone.now()
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
        return product 
        
    ## Most Popular Products
    
class CategoryListAPIView(generics.ListAPIView):
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        return Category.objects.filter(parent__isnull=True, is_active=True).prefetch_related('children')[:9]
    
class SubCategoryListAPIView(generics.ListAPIView):
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        return Category.objects.filter(parent__isnull=False)[:9]


