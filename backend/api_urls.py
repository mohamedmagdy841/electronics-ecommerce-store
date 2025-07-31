from django.urls import path, include, re_path

from accounts.views import CustomLoginView, CustomRegisterView, SendOtpView, VerifyOtpView

urlpatterns = [
    path('accounts/', include('accounts.urls')),
    path('auth/users/login/', CustomLoginView.as_view(), name='custom-login'),
    path("auth/users/", CustomRegisterView.as_view(), name="custom-register"),
    path('auth/users/send-otp/', SendOtpView.as_view(), name='send-otp'),
    path('auth/users/verify-otp/', VerifyOtpView.as_view(), name='verify-otp'),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    re_path(r'^auth/', include('djoser.social.urls')),
]
