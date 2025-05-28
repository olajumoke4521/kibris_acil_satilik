from rest_framework import serializers
from .models import (
    CarAdvertisement, CarImage, CarExplanation,
    CarExternalFeature, CarInternalFeature
)


class CarImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = CarImage
        fields = ('id', 'image',  'is_cover', 'uploaded_at')
        read_only_fields = ('id', 'uploaded_at')

    def get_image(self, obj):
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

class CarBasicSerializer(serializers.ModelSerializer):
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = CarAdvertisement
        fields = ('id', 'title', 'price', 'published_date', 'is_active', 'cover_image')

    def get_cover_image(self, obj):
        cover_image_instance = obj.images.filter(is_cover=True).first()
        if not cover_image_instance:
            cover_image_instance = obj.images.first()

        if cover_image_instance:
            request = self.context.get('request')
            image_serializer_data = CarImageSerializer(cover_image_instance, context={'request': request}).data
            return image_serializer_data.get('image')
        return None

class CarListSerializer(serializers.ModelSerializer):
    """Serializer for PUBLIC car listing view"""
    images = CarImageSerializer(many=True, read_only=True)

    class Meta:
        model = CarAdvertisement
        fields = (
            'id', 'title', 'price', 'price_type',
             'brand', 'series', 'model_year', 'fuel_type', 'transmission', 'city', 'area',
            'images', 'published_date', 'is_active',
        )


class CarAdminListSerializer(CarListSerializer):
    """Serializer for ADMIN car listing view"""
    user_email = serializers.CharField(source='user.email', read_only=True, allow_null=True)

    class Meta(CarListSerializer.Meta):
        fields = CarListSerializer.Meta.fields + (
            'advertise_status', 'user_email', 'created_at'
        )


class CarDetailSerializer(serializers.ModelSerializer):
    """Serializer for DETAILED car view (Public and Admin)"""
    images = CarImageSerializer(many=True, read_only=True)
    explanation = serializers.CharField(source='explanation.explanation', read_only=True, allow_null=True)
    external_features = CarExternalFeatureSerializer(read_only=True, allow_null=True)
    internal_features = CarInternalFeatureSerializer(read_only=True, allow_null=True)


    class Meta:
        model = CarAdvertisement
        fields = '__all__'

class CarAdminCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer used by Admin for Creating and Updating Cars"""
    explanation = serializers.CharField(write_only=True, required=False, allow_blank=True)
    external_features = CarExternalFeatureSerializer(required=False, allow_null=True)
    internal_features = CarInternalFeatureSerializer(required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False, default=True)

    class Meta:
        model = CarAdvertisement
        fields = [
            'title', 'price', 'price_type',
            'brand', 'model_year', 'color', 'transmission', 'series', 'city', 'area', 'vehicle_type', 'advertisement_type',
            'fuel_type', 'steering_type', 'engine_displacement', 'engine_power',
             'advertise_status', 'explanation', 'external_features', 'internal_features', 'is_active'
        ]

        read_only_fields = ('user',)


    def create(self, validated_data):
        external_features_data = validated_data.pop('external_features', None)
        internal_features_data = validated_data.pop('internal_features', None)
        explanation_data = validated_data.pop('explanation', None)

        car_instance = CarAdvertisement.objects.create(**validated_data)

        if external_features_data:
            CarExternalFeature.objects.create(car_ad=car_instance, **external_features_data)

        if internal_features_data:
            CarInternalFeature.objects.create(car_ad=car_instance, **internal_features_data)

        if explanation_data:
            CarExplanation.objects.create(car_ad=car_instance, explanation=explanation_data)

        return car_instance

    def update(self, instance, validated_data):
        external_features_data = validated_data.pop('external_features', None)
        internal_features_data = validated_data.pop('internal_features', None)
        explanation_data = validated_data.pop('explanation', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if external_features_data is not None:
            CarExternalFeature.objects.update_or_create(
                car_ad=instance,
                defaults=external_features_data
            )

        if internal_features_data is not None:
            CarInternalFeature.objects.update_or_create(
                car_ad=instance,
                defaults=internal_features_data
            )

        if explanation_data is not None:
            CarExplanation.objects.update_or_create(
                car_ad=instance,
                defaults={'explanation': explanation_data}
            )

        return instance