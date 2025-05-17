from django_filters import rest_framework as filters

from .models import PropertyAdvertisement


class PropertyFilter(filters.FilterSet):
    minPrice = filters.NumberFilter(field_name="price", lookup_expr='gte')
    maxPrice = filters.NumberFilter(field_name="price", lookup_expr='lte')
    city = filters.CharFilter(field_name="location__province",
                                 lookup_expr='iexact')
    location = filters.CharFilter(field_name="location__district", lookup_expr='iexact',
                                              label="Location (District)")
    type = filters.CharFilter(field_name="property_type", lookup_expr='iexact', label="Property Type")
    roomType = filters.CharFilter(field_name="room_type", lookup_expr='iexact')


    class Meta:
        model = PropertyAdvertisement
        fields = {
            'price': ['gte', 'lte'],
            'location__province': ['exact', 'iexact'],
            'location__district': ['exact', 'iexact'],
            'property_type': ['exact', 'iexact'],
            'room_type': ['exact', 'iexact'],
        }