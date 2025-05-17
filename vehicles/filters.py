from django_filters import rest_framework as filters
from .models import CarAdvertisement


class CarFilter(filters.FilterSet):
    minPrice = filters.NumberFilter(field_name="price", lookup_expr='gte')
    maxPrice = filters.NumberFilter(field_name="price", lookup_expr='lte')
    type = filters.CharFilter(field_name="vehicle_type", lookup_expr='iexact')
    brand = filters.CharFilter(field_name="brand", lookup_expr='iexact')
    series = filters.CharFilter(field_name="series", lookup_expr='iexact')
    modelYear = filters.NumberFilter(field_name="model_year", lookup_expr='gte')

    class Meta:
        model = CarAdvertisement
        fields = {
            'price': ['gte', 'lte'],
            'vehicle_type': ['iexact'],
            'brand': ['iexact'],
            'model_year': ['gte', 'exact'],
        }
