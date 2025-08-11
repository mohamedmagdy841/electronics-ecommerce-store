from django.conf import settings
from django.db import models
from products.models import ProductVariant

class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'variant'],
                name='unique_wishlist_item'
            )
        ]
        
    def __str__(self):
        return f"{self.user.username} - {self.variant.product.name}"

