from rest_framework.permissions import BasePermission, SAFE_METHODS
from accounts.models import User
from .models import Product

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.user_id == request.user.id or request.user.is_staff    

class IsVendor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.VENDOR

class IsVendorOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Product):
            return obj.vendor == request.user
        if hasattr(obj, "product"):  # Variant, Image, Specification
            return obj.product.vendor == request.user
        if hasattr(obj, "variant"):  # VariantSpecification
            return obj.variant.product.vendor == request.user
        return False
