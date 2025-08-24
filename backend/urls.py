from django.contrib import admin
from django.urls import include, path



urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('backend.api_urls')),
    path('api/v1/vendors/', include('backend.vendors_api_urls')),
]
