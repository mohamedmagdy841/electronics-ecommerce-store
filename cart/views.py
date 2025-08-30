from django.db.models import F
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    GenericAPIView,
    DestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.utils import get_or_create_cart
from products.models import ProductVariant
from .serializers import (
    CartItemCreateSerializer,
    CartSerializer,
    WishlistItemSerializer,
    WishlistCreateSerializer,
)
from .models import CartItem, WishlistItem

COOKIE_NAME = "guest_id"
COOKIE_AGE = 60 * 60 * 24 * 30  # 30 days

# -------------------- Wishlist --------------------

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

# -------------------- Cart --------------------

class CartDetailAPIView(RetrieveAPIView):
    permission_classes = [AllowAny]    
    serializer_class = CartSerializer

    def get(self, request, *args, **kwargs):
        cart, new_guest_id = get_or_create_cart(request, cookie_name=COOKIE_NAME)
        response = Response(CartSerializer(cart).data)
        if new_guest_id:
            response.set_cookie(COOKIE_NAME, new_guest_id, max_age=COOKIE_AGE, httponly=True, samesite="Lax") # add secure=True in prod
        return response
   
class CartAddItemAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = CartItemCreateSerializer

    def post(self, request, *args, **kwargs):
        cart, new_guest_id = get_or_create_cart(request, cookie_name=COOKIE_NAME)

        ser = self.get_serializer(data=request.data, context={"cart": cart})
        ser.is_valid(raise_exception=True)
        ser.save()

        resp = Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)
        if new_guest_id:
            resp.set_cookie(COOKIE_NAME, new_guest_id, max_age=COOKIE_AGE,
                            httponly=True, samesite="Lax")  # add secure=True in prod
        return resp

class CartIncrementItemAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = CartSerializer
    
    def post(self, request, pk):
        cart, _ = get_or_create_cart(request, cookie_name=COOKIE_NAME)
        item = get_object_or_404(CartItem.objects.select_related("variant"), pk=pk, cart=cart)
        

        with transaction.atomic():
            variant = ProductVariant.objects.select_for_update().get(pk=item.variant_id)
            item = CartItem.objects.select_for_update().get(pk=item.pk)

            if variant.stock <= 0:
                return Response({"detail": "Out of stock."}, status=status.HTTP_400_BAD_REQUEST)

            target = min(item.quantity + 1, variant.stock)
            if target != item.quantity:
                CartItem.objects.filter(pk=item.pk).update(quantity=target)
            
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class CartDecrementItemAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = CartSerializer
    
    def post(self, request, pk):
        cart, _ = get_or_create_cart(request, cookie_name=COOKIE_NAME)
        item = get_object_or_404(CartItem.objects.select_related("variant"), pk=pk, cart=cart)
        
        with transaction.atomic():
            if item.quantity <= 1:
                item.delete()
            else:
                CartItem.objects.filter(pk=item.pk).update(quantity=F('quantity') - 1)
                
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

class CartRemoveItemAPIView(DestroyAPIView):
    permission_classes = [AllowAny]
    lookup_url_kwarg = "pk"

    def get_object(self):
        cart, _ = get_or_create_cart(self.request, cookie_name=COOKIE_NAME)
        return get_object_or_404(CartItem, pk=self.kwargs["pk"], cart=cart)
