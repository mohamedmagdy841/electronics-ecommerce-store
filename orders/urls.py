from django.urls import path

from .views import ShippingAddressListCreate, ShippingAddressDetail

urlpatterns = [
    path("shipping-addresses/", ShippingAddressListCreate.as_view()),
    path("shipping-addresses/<int:pk>/", ShippingAddressDetail.as_view()),
]
