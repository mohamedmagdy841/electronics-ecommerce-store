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

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiTypes,
)


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

@extend_schema(
    tags=["Wishlist"],
    summary="List my wishlist",
    description="Returns the authenticated user's wishlist items.",
    responses=WishlistItemSerializer,
)
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

@extend_schema(
    tags=["Wishlist"],
    summary="Toggle wishlist item",
    description=(
        "Add the given variant to the wishlist if it is not present; "
        "otherwise remove it. Returns 201 with the item when added, or 204 when removed."
    ),
    request=inline_serializer(
        name="WishlistToggleRequest",
        fields={"variant": WishlistCreateSerializer().fields["variant"]}
    ),
    responses={
        201: WishlistItemSerializer,
        204: OpenApiResponse(description="Removed from wishlist."),
        400: OpenApiResponse(description="Missing or invalid 'variant'."),
        404: OpenApiResponse(description="Variant not found."),
    },
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

@extend_schema(
    tags=["Cart"],
    summary="Get current cart",
    description=(
        "Fetch the current cart. Creates a guest cart and sets a cookie if none exists."
    ),
    auth=[],
    responses=CartSerializer,
)
class CartDetailAPIView(RetrieveAPIView):
    permission_classes = [AllowAny]    
    serializer_class = CartSerializer

    def get(self, request, *args, **kwargs):
        cart, new_guest_id = get_or_create_cart(request, cookie_name=COOKIE_NAME)
        response = Response(CartSerializer(cart).data)
        if new_guest_id:
            response.set_cookie(COOKIE_NAME, new_guest_id, max_age=COOKIE_AGE, httponly=True, samesite="Lax") # add secure=True in prod
        return response

@extend_schema(
    tags=["Cart"],
    summary="Add item to cart",
    description="Create or update a cart line item for the current (guest or authenticated) cart.",
    auth=[],
    request=CartItemCreateSerializer,
    responses={201: CartSerializer, 400: OpenApiResponse(description="Validation error")},
)    
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

@extend_schema(
    tags=["Cart"],
    summary="Increment cart item quantity",
    description="Increase the quantity by 1 (capped at available stock).",
    auth=[],
    parameters=[
        OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH, description="Cart item ID"),
    ],
    responses={200: CartSerializer, 400: OpenApiResponse(description="Out of stock or invalid item"), 404: OpenApiResponse(description="Item not found")},
)
class CartIncrementItemAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    
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

@extend_schema(
    tags=["Cart"],
    summary="Decrement cart item quantity",
    description="Decrease the quantity by 1. If it reaches 0, the item is removed.",
    auth=[],
    parameters=[
        OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH, description="Cart item ID"),
    ],
    responses={200: CartSerializer, 404: OpenApiResponse(description="Item not found")},
)
class CartDecrementItemAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    
    def post(self, request, pk):
        cart, _ = get_or_create_cart(request, cookie_name=COOKIE_NAME)
        item = get_object_or_404(CartItem.objects.select_related("variant"), pk=pk, cart=cart)
        
        with transaction.atomic():
            if item.quantity <= 1:
                item.delete()
            else:
                CartItem.objects.filter(pk=item.pk).update(quantity=F('quantity') - 1)
                
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

@extend_schema(
    tags=["Cart"],
    summary="Remove cart item",
    description="Delete a line item from the cart.",
    auth=[],
    parameters=[
        OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH, description="Cart item ID"),
    ],
    responses={204: OpenApiResponse(description="Deleted"), 404: OpenApiResponse(description="Item not found")},
)
class CartRemoveItemAPIView(DestroyAPIView):
    permission_classes = [AllowAny]
    lookup_url_kwarg = "pk"

    def get_object(self):
        cart, _ = get_or_create_cart(self.request, cookie_name=COOKIE_NAME)
        return get_object_or_404(CartItem, pk=self.kwargs["pk"], cart=cart)
