from django_filters import rest_framework as filters
from .models import CarAdvertisement

class CarFilter(filters.FilterSet):
    price_min = filters.NumberFilter(field_name="price", lookup_expr='gte')
    price_max = filters.NumberFilter(field_name="price", lookup_expr='lte')
    province = filters.CharFilter(field_name="province")
    brand = filters.CharFilter()
    model = filters.CharFilter()
    model_year_min = filters.NumberFilter(field_name="model_year", lookup_expr='gte')
    model_year_max = filters.NumberFilter(field_name="model_year", lookup_expr='lte')
    fuel_type = filters.CharFilter()
    gear_type = filters.CharFilter()
    color = filters.CharFilter()

    class Meta:
        model = CarAdvertisement
        fields = [
            'province', 'brand', 'model', 'price_min', 'price_max',
            'model_year_min', 'model_year_max', 'fuel_type', 'gear_type', 'color'
        ]