from django.urls import path

from accounts.views import (
    VendorLoginView,
    VendorRegisterView,
)
from rest_framework.routers import DefaultRouter
from products.views import (
    VendorProductViewSet,
    VendorProductVariantListCreateView,
    VendorProductVariantRetrieveUpdateDestroyView,
    VendorProductImageListCreateView,
    VendorProductImageDetailView,
    VendorVariantImageListCreateView,
    VendorVariantImageDetailView
)

# Products
router = DefaultRouter()
router.register(r'products', VendorProductViewSet, basename='vendor-products')



urlpatterns = [
    # Auth
    path("auth/", VendorRegisterView.as_view(), name="vendor-register"),
    path("auth/login/", VendorLoginView.as_view(), name="vendor-login"),
    
    path("products/<slug:slug>/variants/", VendorProductVariantListCreateView.as_view()),
    path("products/<slug:slug>/variants/<int:pk>/", VendorProductVariantRetrieveUpdateDestroyView.as_view()),
    # Product images
    path("products/<slug:slug>/images/", VendorProductImageListCreateView.as_view()),
    path("products/<slug:slug>/images/<int:pk>/", VendorProductImageDetailView.as_view()),

    # Variant images
    path("products/<slug:slug>/variants/<int:variant_id>/images/", VendorVariantImageListCreateView.as_view()),
    path("products/<slug:slug>/variants/<int:variant_id>/images/<int:pk>/", VendorVariantImageDetailView.as_view()),
    
]
urlpatterns += router.urls
