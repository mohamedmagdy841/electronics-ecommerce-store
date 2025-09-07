from django.urls import path
from . import views
#from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [
    path("", views.ProductListAPIView.as_view()),
    
    # Home Page
    path("latest/", views.LatestProductListAPIView.as_view()),
    path("weekly-deal/", views.WeeklyDealProductAPIView.as_view()),
    
    path("<slug:slug>/", views.ProductDetailAPIView.as_view()),
    path("related/<slug:slug>/", views.RelatedProductListAPIView.as_view()),
    
    path("<slug:slug>/review/<int:pk>/", views.ProductReviewDetailAPIView.as_view()),
    path("<slug:slug>/reviews/", views.ProductReviewListAPIView.as_view()),
    
] # + debug_toolbar_urls()

