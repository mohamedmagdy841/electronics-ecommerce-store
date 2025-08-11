from django.db.models import Avg, Count, Prefetch, Q
from django.db.models.functions import Coalesce
from rest_framework import generics
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from products.permissions import IsOwnerOrReadOnly
from .models import Brand, Product, Category, ProductImage, ProductReview, ProductVariant
from .serializers import (
    ProductReviewSerializer,
    ProductSerializer,
    ProductDetailSerializer,
    CategorySerializer,
    BrandSerializer
)
from .pagination import CustomProductPagination, RelatedLimitOffset, ReviewCursorPagination
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ProductFilter
from rest_framework import filters
from rest_framework.exceptions import NotFound
from django.utils.functional import cached_property

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
        ).annotate(
                avg_rating=Coalesce(Avg("reviews__rating"), 0.0),
                review_count=Count("reviews", distinct=True),
                # star distribution
                r1=Count("reviews", filter=Q(reviews__rating=1)),
                r2=Count("reviews", filter=Q(reviews__rating=2)),
                r3=Count("reviews", filter=Q(reviews__rating=3)),
                r4=Count("reviews", filter=Q(reviews__rating=4)),
                r5=Count("reviews", filter=Q(reviews__rating=5)),
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
    
class RelatedProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    pagination_class = RelatedLimitOffset
    
    @cached_property
    def product(self):
        slug = self.kwargs['slug']
        try:
            return Product.objects.select_related("category", "brand").get(slug=slug)
        except Product.DoesNotExist:
            raise NotFound("Product not found.")
    
    def get_queryset(self):
        product = self.product
        
        return (Product.objects
                .filter(category=product.category)
                .exclude(id=product.id)
                .select_related("brand")
                .prefetch_related(
                    Prefetch(
                        "images",
                        queryset=(
                            ProductImage.objects
                            .filter(variant__isnull=True)
                            .order_by("-is_primary")
                        ),
                        to_attr="primary_images"
                    ),
                    Prefetch("variants", queryset=ProductVariant.objects.order_by('-is_default','id'))
                )
                .order_by("-is_featured", "-created_at")
                )
         

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

# Product Review 
class ProductReviewListAPIView(generics.ListCreateAPIView):
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = ReviewCursorPagination
    
    @cached_property
    def product(self):
        try:
            return Product.objects.get(slug=self.kwargs['slug'])
        except Product.DoesNotExist:
            raise NotFound("Product not found.")
        
    def get_queryset(self):
        product = self.product
        return (
            ProductReview.objects
            .filter(product=product, parent__isnull=True)
            .select_related('user')
            .prefetch_related(
                Prefetch(
                    'replies',
                    queryset=ProductReview.objects.select_related('user').order_by('created_at', 'id')
                )
            )
            .order_by("-created_at", "-id")
        )
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['product'] = self.product
        return context

class ProductReviewDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductReview.objects.select_related("user", "product")
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    
