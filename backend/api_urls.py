from django.urls import path, include

from accounts.views import (
    CustomLoginView,
    CustomRegisterView,
    SendOtpView, VerifyOtpView
)

from products.views import (
    CategoryListAPIView,
    SubCategoryListAPIView,
    BrandListAPIView,
    SubcategoryListByCategoryAPIView
)

urlpatterns = [
    # Accounts
    path('accounts/', include('accounts.urls')),
    path('auth/users/login/', CustomLoginView.as_view(), name='custom-login'),
    path("auth/users/", CustomRegisterView.as_view(), name="custom-register"),
    path('auth/users/send-otp/', SendOtpView.as_view(), name='send-otp'),
    path('auth/users/verify-otp/', VerifyOtpView.as_view(), name='verify-otp'),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('auth/', include('djoser.social.urls')),
    
    # Products
    path('products/', include('products.urls')),
    
    # Categories
    path("categories/", CategoryListAPIView.as_view()),
    path("subcategories/", SubCategoryListAPIView.as_view()),
    path("categories/<slug:slug>/subcategories/", SubcategoryListByCategoryAPIView.as_view()),
    
    # Brands
    path("brands/", BrandListAPIView.as_view())
]
