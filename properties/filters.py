from django_filters import rest_framework as filters

from .models import PropertyAdvertisement


class PropertyFilter(filters.FilterSet):
    price_min = filters.NumberFilter(field_name="price", lookup_expr='gte')
    price_max = filters.NumberFilter(field_name="price", lookup_expr='lte')
    province = filters.CharFilter(field_name="location__province")
    district = filters.CharFilter(field_name="location__district")
    neighborhood = filters.CharFilter(field_name="location__neighborhood")
    property_type = filters.CharFilter()
    room_type = filters.CharFilter()
    building_age = filters.NumberFilter()
    warming_type = filters.CharFilter()
    furnished = filters.BooleanFilter()
    has_elevator = filters.BooleanFilter(field_name="external_features__elevator")
    has_balcony = filters.BooleanFilter(field_name="interior_features__balcony")
    has_garden = filters.BooleanFilter(field_name="external_features__gardened")

    class Meta:
        model = PropertyAdvertisement
        fields = [
            'province', 'district', 'neighborhood', 'property_type',
            'room_type', 'price_min', 'price_max',
            'building_age', 'furnished', 'has_elevator', 'has_balcony',
            'has_garden'
        ]