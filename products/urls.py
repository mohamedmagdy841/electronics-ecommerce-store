from django.urls import path
from . import views
from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [
    path("", views.ProductListAPIView().as_view()),
    path("<slug:slug>/", views.ProductDetailAPIView().as_view()),
] + debug_toolbar_urls()

