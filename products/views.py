from django.db.models import Avg, Count, Prefetch, Q
from django.db.models.functions import Coalesce
from rest_framework import generics, viewsets
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from .permissions import IsOwnerOrReadOnly, IsVendor, IsVendorOwner
from .models import (
    Brand, Product, Category, ProductImage,
    ProductReview, ProductSpecification,
    ProductVariant, VariantSpecification,
)
from .serializers import (
    ProductReviewSerializer,
    ProductSerializer,
    ProductDetailSerializer,
    CategorySerializer,
    BrandSerializer,
    VendorProductImageSerializer,
    VendorProductSerializer,
    VendorProductSpecificationSerializer,
    VendorProductVariantSerializer,
    VendorVariantSpecificationSerializer,
    VendorCategorySerializer,
    VendorBrandSerializer,
)
from .pagination import CustomProductPagination, RelatedLimitOffset, ReviewCursorPagination
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ProductFilter
from rest_framework import filters
from rest_framework.exceptions import NotFound, PermissionDenied
from django.utils.functional import cached_property
from rest_framework.parsers import MultiPartParser, FormParser

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
)

# -------------------- Products --------------------

@extend_schema(
    tags=["Products"],
    summary="List products",
    description=(
        "List products with filtering, search and ordering.\n\n"
        "**Search fields:** name, description, brand__name, category__name, sku\n"
        "**Ordering fields:** price, created_at"
    ),
    parameters=[
        OpenApiParameter(name="search", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
        OpenApiParameter(name="ordering", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
    ],
)
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

@extend_schema(
    tags=["Products"],
    summary="Retrieve product detail",
    parameters=[
        OpenApiParameter("slug", OpenApiTypes.STR, OpenApiParameter.PATH, description="Product slug"),
        OpenApiParameter("variant", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False,
                         description="Optional variant ID to tailor the response"),
    ],
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

@extend_schema(
    tags=["Products"],
    summary="List related products",
    parameters=[
        OpenApiParameter("slug", OpenApiTypes.STR, OpenApiParameter.PATH, description="Slug of the reference product"),
    ],
)  
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
         

# -------------------- Home Page Views --------------------

@extend_schema(
    tags=["Home"],
    summary="Latest products",
    description="Returns the most recently created products (cached).",
)
class LatestProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        products = cache.get("latest_products")
        
        if products is None:
            products = Product.objects.prefetch_related('images').order_by('-created_at')[:9]
            cache.set("latest_products", products, timeout=60*60)
            
        return products

@extend_schema(
    tags=["Home"],
    summary="Weekly deal product",
    description="Returns the active weekly-deal product (cached).",
)  
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

# -------------------- Categories & Brands --------------------   

@extend_schema(
    tags=["Categories"],
    summary="List top-level categories",
    description="Returns root categories with their children (cached).",
)
class CategoryListAPIView(generics.ListAPIView):
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        categories = cache.get("category_list")
        
        if categories is None:
            categories = Category.objects.filter(parent__isnull=True, is_active=True).prefetch_related('children')[:9]
            cache.set("category_list", categories, timeout=60*60)

        return categories

@extend_schema(
    tags=["Categories"],
    summary="List subcategories by parent",
    parameters=[
        OpenApiParameter("slug", OpenApiTypes.STR, OpenApiParameter.PATH, description="Parent category slug"),
    ],
)   
class SubcategoryListByCategoryAPIView(generics.ListAPIView):
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        parent_slug = self.kwargs['slug']
        return Category.objects.filter(parent__slug=parent_slug)   

@extend_schema(
    tags=["Categories"],
    summary="List subcategories",
    description="Returns subcategories (non-root) (cached).",
)
class SubCategoryListAPIView(generics.ListAPIView):
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        categories = cache.get("subcategory_list")
        
        if categories is None:
            categories = Category.objects.filter(parent__isnull=False)[:9]
            cache.set("subcategory_list", categories, timeout=60*60)
            
        return categories 
    
@extend_schema(
    tags=["Brands"],
    summary="List brands",
)
class BrandListAPIView(generics.ListAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer

# -------------------- Reviews --------------------

@extend_schema_view(
    get=extend_schema(
        tags=["Reviews"],
        summary="List product reviews",
        parameters=[OpenApiParameter("slug", OpenApiTypes.STR, OpenApiParameter.PATH, description="Product slug")],
        description="Cursor-paginated top-level reviews. Replies are nested under each review.",
    ),
    post=extend_schema(
        tags=["Reviews"],
        summary="Create a product review",
        description="Authenticated users can create a top-level review for the given product.",
    ),
)
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
    
@extend_schema(
    tags=["Reviews"],
    summary="Retrieve/Update/Delete a review",
)
class ProductReviewDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    
    @cached_property
    def product(self):
        try:
            return Product.objects.get(slug=self.kwargs["slug"])
        except Product.DoesNotExist:
            raise NotFound("Product not found.")
        
    def get_queryset(self):
        product = self.product
        return (
            ProductReview.objects
            .filter(product=product)
            .select_related('user', 'product')
            .prefetch_related(
                Prefetch(
                    'replies',
                    queryset=ProductReview.objects.select_related('user').order_by('created_at', 'id')
                )
            )
        )
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["product"] = self.product
        return context


# --------------- Vendor ----------------------
# Products
class VendorProductViewSet(viewsets.ModelViewSet):
    serializer_class = VendorProductSerializer
    permission_classes = [IsVendor, IsVendorOwner]

    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user)


class VendorProductVariantListCreateView(generics.ListCreateAPIView):
    serializer_class = VendorProductVariantSerializer
    permission_classes = [IsVendor, IsVendorOwner]
    
    @cached_property
    def product(self):
        try:
            return Product.objects.get(slug=self.kwargs['slug'], vendor=self.request.user)
        except Product.DoesNotExist:
            raise NotFound("Product not found.")
        
    def get_queryset(self):
        return ProductVariant.objects.filter(product=self.product)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['product'] = self.product
        return context

class VendorProductVariantRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VendorProductVariantSerializer
    permission_classes = [IsVendor, IsVendorOwner]
    
    @cached_property
    def product(self):
        try:
            return Product.objects.get(slug=self.kwargs['slug'], vendor=self.request.user)
        except Product.DoesNotExist:
            raise NotFound("Product not found.")
        
    def get_queryset(self):
        return ProductVariant.objects.filter(product=self.product)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['product'] = self.product
        return context

class VendorProductImageListCreateView(generics.ListCreateAPIView):
    serializer_class = VendorProductImageSerializer
    permission_classes = [IsVendor, IsVendorOwner]
    parser_classes = [MultiPartParser, FormParser]
    
    @cached_property
    def product(self):
        return get_object_or_404(Product, slug=self.kwargs["slug"], vendor=self.request.user)

    def get_queryset(self):
        return ProductImage.objects.filter(product=self.product, variant__isnull=True)  # product-only images

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["product"] = self.product
        return context


class VendorProductImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VendorProductImageSerializer
    permission_classes = [IsVendor, IsVendorOwner]
    parser_classes = [MultiPartParser, FormParser]
    
    @cached_property
    def product(self):
        return get_object_or_404(Product, slug=self.kwargs["slug"], vendor=self.request.user)

    def get_queryset(self):
        return ProductImage.objects.filter(product=self.product, variant__isnull=True)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["product"] = self.product
        return context


class VendorVariantImageListCreateView(generics.ListCreateAPIView):
    serializer_class = VendorProductImageSerializer
    permission_classes = [IsVendor, IsVendorOwner]
    parser_classes = [MultiPartParser, FormParser]
    
    @cached_property
    def product(self):
        prod = get_object_or_404(Product, slug=self.kwargs["slug"], vendor=self.request.user)
        print("prod", prod)
        return prod
    
    @cached_property
    def variant(self):
        var = get_object_or_404(ProductVariant, pk=self.kwargs["variant_id"], product=self.product)
        print("var", var)
        return var
    
    def get_queryset(self):
        return ProductImage.objects.filter(
        product=self.product,
        variant=self.variant
    )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["product"] = self.product
        context["variant"] = self.variant
        return context


class VendorVariantImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VendorProductImageSerializer
    permission_classes = [IsVendor, IsVendorOwner]
    parser_classes = [MultiPartParser, FormParser]

    @cached_property
    def product(self):
        return get_object_or_404(Product, slug=self.kwargs["slug"], vendor=self.request.user)

    @cached_property
    def variant(self):
        return get_object_or_404(ProductVariant, pk=self.kwargs["variant_id"], product=self.product)

    def get_queryset(self):
        return ProductImage.objects.filter(
        product=self.product,
        variant=self.variant
    )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["product"] = self.product
        context["variant"] = self.variant
        return context

# Category
class VendorCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = VendorCategorySerializer
    permission_classes = [IsVendor]
    
    def get_queryset(self):
        return Category.objects.filter(vendor=self.request.user).prefetch_related('children')

class VendorBrandViewSet(viewsets.ModelViewSet):
    serializer_class = VendorBrandSerializer
    permission_classes = [IsAuthenticated, IsVendor]

    def get_queryset(self):
        return Brand.objects.filter(vendor=self.request.user)
