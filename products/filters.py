import django_filters
from .models import Product

class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='iexact')
    brand = django_filters.CharFilter(field_name='brand__name', lookup_expr='iexact')
    category = django_filters.CharFilter(field_name='category__name', lookup_expr='iexact')
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')

    class Meta:
        model = Product
        fields = ['name', 'brand', 'category', 'price_min', 'price_max']
