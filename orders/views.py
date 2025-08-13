from django.db import transaction
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from .models import ShippingAddress
from .serializers import ShippingAddressSerializer

class ShippingAddressListCreate(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ShippingAddressSerializer

    def get_queryset(self):
        return (ShippingAddress.objects.filter(user=self.request.user)
                .order_by('-is_default', '-created_at'))

class ShippingAddressDetail(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ShippingAddressSerializer
    
    def get_queryset(self):
        return ShippingAddress.objects.filter(user=self.request.user)
    
    def perform_destroy(self, instance):
        user = instance.user
        was_default = instance.is_default
        super().perform_destroy(instance)
        if was_default:
            with transaction.atomic():
                candidate = (ShippingAddress.objects
                            .select_for_update(skip_locked=True)
                            .filter(user=user)
                            .order_by('-created_at')
                            .first())
                if candidate and not candidate.is_default:
                    candidate.is_default = True
                    candidate.save(update_fields=['is_default'])
