
from rest_framework import serializers
from .models import (
    CarAdvertisement, CarImage, CarExplanation,
    CarExternalFeature, CarInternalFeature
)
from accounts.serializers import CustomerSerializer


class CarImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = CarImage
        fields = ('id', 'image', 'image_url', 'is_cover', 'uploaded_at')
        read_only_fields = ('id', 'image_url', 'uploaded_at')

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None



class CarExplanationSerializer(serializers.ModelSerializer):

    class Meta:
        model = CarExplanation
        fields = ('explanation',)


class CarExternalFeatureSerializer(serializers.ModelSerializer):

    class Meta:
        model = CarExternalFeature
        exclude = ('id', 'car_ad')


class CarInternalFeatureSerializer(serializers.ModelSerializer):

    class Meta:
        model = CarInternalFeature
        exclude = ('id', 'car_ad')

class CarListSerializer(serializers.ModelSerializer):
    """Serializer for PUBLIC car listing view"""
    cover_image_url = serializers.SerializerMethodField()
    location_display = serializers.SerializerMethodField()

    class Meta:
        model = CarAdvertisement
        fields = (
            'id', 'advertise_no', 'title', 'price', 'price_type',
            'location_display',
            'brand', 'model', 'model_year', 'fuel_type', 'gear_type',
            'cover_image_url', 'published_date',
        )

    def get_cover_image_url(self, obj):
        cover = obj.images.filter(is_cover=True).first()
        request = self.context.get('request')
        if cover and cover.image:
            return request.build_absolute_uri(cover.image.url) if request else cover.image.url
        first_image = obj.images.first()
        if first_image and first_image.image:
             return request.build_absolute_uri(first_image.image.url) if request else first_image.image.url
        return None

    def get_location_display(self, obj):
        parts = [obj.province]

        if obj.address_detail:
             parts.append(obj.address_detail[:30] + "...")
        return ' / '.join(part for part in parts if part)


class CarAdminListSerializer(CarListSerializer):
    """Serializer for ADMIN car listing view"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True, allow_null=True)

    class Meta(CarListSerializer.Meta):
        fields = CarListSerializer.Meta.fields + (
            'advertise_status', 'customer_name', 'user_email', 'created_at'
        )


class CarDetailSerializer(serializers.ModelSerializer):
    """Serializer for DETAILED car view (Public and Admin)"""
    images = CarImageSerializer(many=True, read_only=True)
    explanation = serializers.CharField(source='explanation.explanation', read_only=True, allow_null=True)
    external_features = CarExternalFeatureSerializer(read_only=True, allow_null=True)
    internal_features = CarInternalFeatureSerializer(read_only=True, allow_null=True)
    customer = CustomerSerializer(read_only=True)

    class Meta:
        model = CarAdvertisement
        fields = '__all__'


class CarAdminCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer used by Admin for Creating and Updating Cars"""

    customer_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    explanation = serializers.CharField(write_only=True, required=False, allow_blank=True)
    external_features = CarExternalFeatureSerializer(required=False, allow_null=True)
    internal_features = CarInternalFeatureSerializer(required=False, allow_null=True)

    class Meta:
        model = CarAdvertisement
        fields = [
            'title', 'price', 'price_type', 'province', 'address',
            'brand', 'model', 'model_year', 'color', 'gear_type',
            'fuel_type', 'steering_type', 'engine_displacement', 'engine_power',
             'advertise_status',
            'customer_id',
            'explanation', 'external_features', 'internal_features',
        ]