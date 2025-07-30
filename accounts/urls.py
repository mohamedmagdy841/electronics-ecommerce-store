from django.urls import path, include
from .views import CustomLoginView

urlpatterns = [
    path('auth/login/', CustomLoginView.as_view(), name='custom-login'),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')), 
]
