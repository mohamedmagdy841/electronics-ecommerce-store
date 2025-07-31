from django.urls import path, include

from accounts.views import CustomLoginView

urlpatterns = [
    path('accounts/', include('accounts.urls')),
    path('auth/login/', CustomLoginView.as_view(), name='custom-login'),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')), 
]
