from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import ProductVariant
from .serializers import WishlistItemSerializer, WishlistCreateSerializer
from .models import WishlistItem

class WishlistListAPIView(ListAPIView):
    serializer_class = WishlistItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return (
            WishlistItem.objects
            .filter(user=self.request.user)
            .select_related('variant', 'variant__product')
            .prefetch_related(
                'variant__images',
            )
        )

class WishlistToggleAPIView(APIView):
    serializer_class = WishlistCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        variant = request.data.get('variant')
        if not variant:
            return Response({"detail": "variant field is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        variant = get_object_or_404(ProductVariant.objects.select_related('product'), id=variant)
        
        item = WishlistItem.objects.filter(user=request.user, variant=variant).first()
        if item:
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        new_item = WishlistItem.objects.create(user=request.user, variant=variant)
        return Response(WishlistItemSerializer(new_item).data, status=status.HTTP_201_CREATED)
