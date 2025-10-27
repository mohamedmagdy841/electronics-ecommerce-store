from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok"}, status=200)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('backend.api_urls')),
    path('api/v1/vendors/', include('backend.vendors_api_urls')),
    path("health/", health_check), 
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
