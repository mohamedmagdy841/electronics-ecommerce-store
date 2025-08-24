from django.urls import path
from accounts.views import (
    VendorLoginView,
    VendorRegisterView,
)
from rest_framework.routers import DefaultRouter
from products.views import (
    VendorProductViewSet,
    VendorProductVariantListCreateView,
    VendorProductVariantRetrieveUpdateDestroyView
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
]
urlpatterns += router.urls
