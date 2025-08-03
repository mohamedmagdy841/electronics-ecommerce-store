from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Product, Category

@receiver([post_save, post_delete], sender=Product)
def ivalidate_product_cache(sender, **kwargs):
    cache.delete("latest_products")
    cache.delete("weekly_deal_product")

@receiver([post_save, post_delete], sender=Category)
def ivalidate_category_cache(sender, **kwargs):
    cache.delete("category_list")
    cache.delete("subcategory_list")
