from django.urls import path

from .views import (
    ShippingAddressListCreate,
    ShippingAddressDetail,
    CouponListCreateView,
    CouponDetailView,
    PublicCouponListView,
)

urlpatterns = [
    path("shipping-addresses/", ShippingAddressListCreate.as_view()),
    path("shipping-addresses/<int:pk>/", ShippingAddressDetail.as_view()),
    
    # Coupons
    path("coupons/", CouponListCreateView.as_view()),
    path("coupons/<int:pk>/", CouponDetailView.as_view()),
    path("public/coupons/", PublicCouponListView.as_view()),
]
