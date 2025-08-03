from rest_framework import generics
from .models import Product
from .serializers import (
    ProductSerializer
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
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Product.objects.select_related(
            'category', 'brand'
        ).prefetch_related(
            'images', 'specs__specification', 'category__children'
        )

