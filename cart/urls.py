from django.urls import path

from .views import (
    CartDetailAPIView,
    CartAddItemAPIView,
    CartIncrementItemAPIView,
    CartDecrementItemAPIView,
    CartRemoveItemAPIView,
)

urlpatterns = [
    path("", CartDetailAPIView.as_view()),                   
    path("add/", CartAddItemAPIView.as_view()),   
    path("<int:pk>/increment/", CartIncrementItemAPIView.as_view()),
    path("<int:pk>/decrement/", CartDecrementItemAPIView.as_view()),
    path("<int:pk>/delete/", CartRemoveItemAPIView.as_view()), 
]
