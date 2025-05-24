
from django_filters import rest_framework as filters
from .models import Offer, CarOffer, PropertyOffer

class OfferFilter(filters.FilterSet):
    offer_type = filters.ChoiceFilter(choices=Offer.OFFER_TYPE_CHOICES)
    city = filters.CharFilter(lookup_expr='icontains')
    area = filters.CharFilter(lookup_expr='icontains')
    full_name = filters.CharFilter(lookup_expr='icontains')
    email = filters.CharFilter(lookup_expr='iexact')
    phone = filters.CharFilter(lookup_expr='icontains')
    is_active = filters.BooleanFilter()

    min_price = filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = filters.NumberFilter(field_name="price", lookup_expr='lte')


    car_model = filters.CharFilter(field_name='car_details__model', lookup_expr='icontains', label='Car Model')
    car_brand = filters.CharFilter(field_name='car_details__brand', lookup_expr='icontains', label='Car Brand')
    min_kilometer = filters.NumberFilter(field_name='car_details__kilometer', lookup_expr='gte', label='Min Kilometers')
    max_kilometer = filters.NumberFilter(field_name='car_details__kilometer', lookup_expr='lte', label='Max Kilometers')
    min_model_year = filters.NumberFilter(field_name='car_details__model_year', lookup_expr='gte', label='Min Car Model Year')
    max_model_year = filters.NumberFilter(field_name='car_details__model_year', lookup_expr='lte', label='Max Car Model Year')
    car_fuel_type = filters.ChoiceFilter(field_name='car_details__fuel_type', choices=CarOffer.FUEL_TYPE_CHOICES, label='Car Fuel Type')
    car_transmission = filters.ChoiceFilter(field_name='car_details__transmission', choices=CarOffer.TRANSMISSION_CHOICES, label='Car Transmission')

    property_address = filters.CharFilter(field_name='property_details__address', lookup_expr='icontains', label='Property Address')
    property_room_type = filters.ChoiceFilter(field_name='property_details__room_type', choices=PropertyOffer.ROOM_TYPE_CHOICES, label='Property Room Type')
    property_document_type = filters.ChoiceFilter(field_name='property_details__document_type', choices=PropertyOffer.DOCUMENT_TYPE_CHOICES, label='Property Document Type')
    min_square_meter = filters.NumberFilter(field_name='property_details__square_meter', lookup_expr='gte', label='Min Square Meters')
    max_square_meter = filters.NumberFilter(field_name='property_details__square_meter', lookup_expr='lte', label='Max Square Meters')


    class Meta:
        model = Offer
        fields = [
            'offer_type',
            'city',
            'area',
            'full_name',
            'email',
            'phone',
            'is_active',
            'min_price', 'max_price',
            'car_model', 'car_brand', 'min_kilometer', 'max_kilometer', 'min_model_year', 'max_model_year', 'car_fuel_type', 'car_transmission',
            'property_address', 'property_room_type', 'property_document_type', 'min_square_meter', 'max_square_meter',
        ]