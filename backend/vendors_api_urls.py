from django.urls import path
from accounts.views import (
    VendorLoginView,
    VendorRegisterView,
)
from rest_framework.routers import DefaultRouter
from products.views import (
    VendorProductViewSet,
    VendorProductVariantViewSet,
    VendorProductImageViewSet,
    VendorProductSpecificationViewSet,
    VendorVariantSpecificationViewSet,
)

# Products
router = DefaultRouter()
router.register(r'products', VendorProductViewSet, basename='vendor-products')
router.register(r'variants', VendorProductVariantViewSet, basename='vendor-variants')
router.register(r'images', VendorProductImageViewSet, basename='vendor-images')
router.register(r'product-specs', VendorProductSpecificationViewSet, basename='vendor-product-specs')
router.register(r'variant-specs', VendorVariantSpecificationViewSet, basename='vendor-variant-specs')


urlpatterns = [
    # Auth
    path("auth/", VendorRegisterView.as_view(), name="vendor-register"),
    path("auth/login/", VendorLoginView.as_view(), name="vendor-login"),
]
urlpatterns += router.urls
