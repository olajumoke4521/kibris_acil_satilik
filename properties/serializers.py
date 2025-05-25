from rest_framework import serializers
from .models import (
    PropertyAdvertisement, PropertyImage, PropertyExplanation, Location,
    PropertyExternalFeature, PropertyInteriorFeature
)
from vehicles.models import CarAdvertisement
from vehicles.serializers import CarListSerializer


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'city', 'area')

class PropertyImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = PropertyImage
        fields = ('id', 'image', 'is_cover', 'uploaded_at')
        read_only_fields = ('id', 'uploaded_at')

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class PropertyExplanationSerializer(serializers.ModelSerializer):

    class Meta:
        model = PropertyExplanation
        fields = ('explanation',)

class PropertyExternalFeatureSerializer(serializers.ModelSerializer):

    class Meta:
        model = PropertyExternalFeature
        exclude = ('id', 'property_ad')


class PropertyInteriorFeatureSerializer(serializers.ModelSerializer):

    class Meta:
        model = PropertyInteriorFeature
        exclude = ('id', 'property_ad')

class PropertyBasicSerializer(serializers.ModelSerializer):
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = PropertyAdvertisement
        fields = ('id', 'title', 'price', 'published_date', 'is_active', 'cover_image')

    def get_cover_image(self, obj):
        cover_image_instance = obj.images.filter(is_cover=True).first()
        if not cover_image_instance:
            cover_image_instance = obj.images.first()

        if cover_image_instance:
            request = self.context.get('request')
            image_serializer_data = PropertyImageSerializer(cover_image_instance, context={'request': request}).data
            return image_serializer_data.get('image_url')
        return None

class PropertyListSerializer(serializers.ModelSerializer):
    """Serializer for PUBLIC listing view"""
    images = PropertyImageSerializer(many=True, read_only=True)
    location_str = serializers.CharField(source='location.__str__', read_only=True)

    class Meta:
        model = PropertyAdvertisement
        fields = ('id', 'title', 'price', 'price_currency', 'address', 'location_str', 'property_type', 'advertisement_type', 'room_type','gross_area', 'net_area', 'images', 'published_date')


class PropertyAdminListSerializer(PropertyListSerializer):
     user_email = serializers.CharField(source='user.email', read_only=True, allow_null=True)

     class Meta(PropertyListSerializer.Meta):
        fields = PropertyListSerializer.Meta.fields + (
            'advertise_status', 'user_email', 'created_at'
        )

class PropertyDetailSerializer(serializers.ModelSerializer):
    """Serializer for DETAILED view (Public and Admin)"""
    images = PropertyImageSerializer(many=True, read_only=True)
    explanation = PropertyExplanationSerializer(read_only=True)
    external_features = PropertyExternalFeatureSerializer(read_only=True, allow_null=True)
    interior_features = PropertyInteriorFeatureSerializer(read_only=True, allow_null=True)
    location = LocationSerializer(read_only=True)

    class Meta:
        model = PropertyAdvertisement
        fields = '__all__'
        read_only_fields = ('id', 'user', 'created_at', 'updated_at', 'published_date')


class PropertyAdminCreateUpdateSerializer(serializers.ModelSerializer):
    external_features = PropertyExternalFeatureSerializer(required=False, allow_null=True)
    interior_features = PropertyInteriorFeatureSerializer(required=False, allow_null=True)
    city = serializers.CharField(write_only=True, required=True, max_length=100)
    area = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=100)
    explanation = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False, default=True)

    class Meta:
        model = PropertyAdvertisement
        exclude = ('id', 'created_at', 'updated_at', 'published_date', 'location')
        read_only_fields = ('user',)

    def create(self, validated_data):

        external_features_data = validated_data.pop('external_features', None)
        interior_features_data = validated_data.pop('interior_features', None)
        explanation_data = validated_data.pop('explanation', None)

        validated_data.pop('city', None)
        validated_data.pop('area', None)

        property_instance = PropertyAdvertisement.objects.create(**validated_data)

        if external_features_data:
            PropertyExternalFeature.objects.create(property_ad=property_instance, **external_features_data)

        if interior_features_data:
            PropertyInteriorFeature.objects.create(property_ad=property_instance, **interior_features_data)

        if explanation_data:
            PropertyExplanation.objects.create(property_ad=property_instance, explanation=explanation_data)

        return property_instance

    def update(self, instance, validated_data):
        external_features_data = validated_data.pop('external_features', None)
        interior_features_data = validated_data.pop('interior_features', None)
        explanation_data = validated_data.pop('explanation', None)

        validated_data.pop('city', None)
        validated_data.pop('area', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if external_features_data is not None:
            PropertyExternalFeature.objects.update_or_create(
                property_ad=instance,
                defaults=external_features_data
            )

        if interior_features_data is not None:
            PropertyInteriorFeature.objects.update_or_create(
                property_ad=instance,
                defaults=interior_features_data
            )

        if explanation_data is not None:
            PropertyExplanation.objects.update_or_create(
                property_ad=instance,
                defaults={'explanation': explanation_data}
            )

        return instance

class LatestAdvertisementSerializer(serializers.Serializer):
    def to_representation(self, instance):
        request = self.context.get('request')
        representation = None

        if isinstance(instance, PropertyAdvertisement):
            serializer = PropertyListSerializer(instance, context={'request': request})
            representation = serializer.data
        elif isinstance(instance, CarAdvertisement):
            serializer = CarListSerializer(instance, context={'request': request})
            representation = serializer.data
            representation['advertisement_type'] = 'car'
        else:
            return None

        return representation