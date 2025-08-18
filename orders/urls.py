from django.urls import path

from .views import (
    ShippingAddressListCreate,
    ShippingAddressDetail,
    CouponListCreateView,
    CouponDetailView,
    PublicCouponListView,
    OrderListView,
    OrderCreateView,
    OrderDetailView,
    OrderItemListView,
    PaymentDetailView,
    PaymentCallbackView,
    InvoiceListView,
    InvoiceDetailView,
)

urlpatterns = [
    path("shipping-addresses/", ShippingAddressListCreate.as_view()),
    path("shipping-addresses/<int:pk>/", ShippingAddressDetail.as_view()),
    
    # Coupons
    path("coupons/", CouponListCreateView.as_view()),
    path("coupons/<int:pk>/", CouponDetailView.as_view()),
    path("public/coupons/", PublicCouponListView.as_view()),
    
    # Orders
    path('', OrderListView.as_view()),
    path('checkout/', OrderCreateView.as_view()),
    path('<int:pk>/', OrderDetailView.as_view()),
    path('<int:order_id>/items/', OrderItemListView.as_view()),
    path('<int:pk>/payment/', PaymentDetailView.as_view()),
    path("payments/callback/<str:gateway_type>/", PaymentCallbackView.as_view()),
    
    # Invoices
    path('invoices/', InvoiceListView.as_view()),
    path('invoices/<int:pk>/', InvoiceDetailView.as_view()),
]
