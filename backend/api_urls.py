from django.urls import path, include

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

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

from cart.views import (
    WishlistListAPIView,
    WishlistToggleAPIView
)

urlpatterns = [
    # Swagger
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
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
    path("brands/", BrandListAPIView.as_view()),
    
    # Cart
    path("cart/", include('cart.urls')),
    
    # Wishlist
    path("wishlist/", WishlistListAPIView.as_view()),
    path("wishlist/toggle/", WishlistToggleAPIView.as_view()),
    
    # Orders
    path("orders/", include('orders.urls')),
]
