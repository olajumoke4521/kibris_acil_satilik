from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import OfferImage, Offer, OfferResponse, PropertyOffer, CarOffer
from django.contrib.auth import get_user_model

User = get_user_model()
class UserSerializer(serializers.ModelSerializer):
    """Serializer for User objects"""
    photo = serializers.ImageField(max_length=None, use_url=True, required=False, allow_null=True)
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('id', 'email', 'phone', 'date_of_membership', 'photo',  'password', 'password_confirm')
        read_only_fields = ('id', 'date_of_membership')

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        if password or password_confirm:
            if not password:
                raise serializers.ValidationError({"password": "This field is required when changing password."})
            if not password_confirm:
                raise serializers.ValidationError(
                    {"password_confirm": "This field is required when changing password."})
            if password != password_confirm:
                raise serializers.ValidationError({"password": "Password fields didn't match."})
        elif 'password' in attrs:
            attrs.pop('password', None)
            attrs.pop('password_confirm', None)

        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        validated_data.pop('password_confirm', None)

        if password:
            instance.set_password(password)

        return super().update(instance, validated_data)

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    photo = serializers.ImageField(max_length=None, use_url=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm', 'phone', 'photo')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        photo = validated_data.pop('photo', None)

        email = validated_data.pop('email', None)

        if not email:
            raise serializers.ValidationError({"email": "Email is required."})

        user = User.objects.create_user(
            email=email,
            password=password,
            **validated_data
        )

        if photo:
            user.photo = photo
            user.save()

        return user

class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                email=email, password=password)

            if not user:
                msg = 'Unable to log in with provided credentials.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Must include "email" and "password".'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class CarOfferDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarOffer
        fields = ['model', 'kilometer', 'model_year', 'brand', 'fuel_type', 'transmission']


class PropertyOfferDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyOffer
        fields = ['address', 'build_date', 'square_meter', 'document_type', 'room_type']


class OfferImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = OfferImage
        fields = ['id', 'image', 'is_cover_image', 'is_active', 'uploaded_at', 'offer']
        read_only_fields = ['id', 'uploaded_at']
        extra_kwargs = {'offer': {'write_only': True, 'required': False}}

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url') and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class OfferResponseSerializer(serializers.ModelSerializer):
    created_by_details = UserSerializer(source='created_by', read_only=True)
    offered_by_details = UserSerializer(source='offered_by', read_only=True)

    created_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='created_by', write_only=True, required=False, allow_null=True
    )
    offered_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='offered_by', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = OfferResponse
        fields = [
            'id', 'offer', 'price', 'currency', 'description', 'offer_date',
            'created_by_details',
            'created_by_id',
            'offered_by_details',
            'offered_by_id',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'offer', 'created_at', 'updated_at', 'created_by_details', 'offered_by_details']


    def create(self, validated_data):

        return super().create(validated_data)

    def update(self, instance, validated_data):

        return super().update(instance, validated_data)

class UserOfferCreateSerializer(serializers.ModelSerializer):
    # Car specific fields (conditionally required)
    model = serializers.CharField(max_length=100, required=False, allow_null=True)
    brand = serializers.CharField(max_length=100, required=False, allow_null=True)
    fuel_type = serializers.ChoiceField(choices=CarOffer.FUEL_TYPE_CHOICES, required=False, allow_null=True)
    transmission = serializers.ChoiceField(choices=CarOffer.TRANSMISSION_CHOICES, required=False, allow_null=True)
    kilometer = serializers.IntegerField(required=False, allow_null=True)
    model_year = serializers.IntegerField(required=False, allow_null=True)

    # Property specific fields (conditionally required)
    address = serializers.CharField(required=False, allow_null=True)
    build_date = serializers.IntegerField(required=False, allow_null=True)
    square_meter = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    room_type = serializers.ChoiceField(choices=PropertyOffer.ROOM_TYPE_CHOICES, required=False, allow_null=True)
    document_type = serializers.ChoiceField(choices=PropertyOffer.DOCUMENT_TYPE_CHOICES, required=False, allow_null=True)

    images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )

    class Meta:
        model = Offer
        fields = [
            'full_name', 'email', 'phone', 'details', 'offer_type', 'city', 'area', 'price',
            'model', 'kilometer', 'model_year', 'fuel_type', 'transmission', 'brand',
            'address', 'build_date', 'square_meter', 'room_type', 'document_type',
            'images'
        ]

    def validate(self, attrs):
        offer_type = attrs.get('offer_type')

        if not attrs.get('email') and not attrs.get('phone'):
            raise serializers.ValidationError("Either email or phone number must be provided.")

        if offer_type == 'car':
            required_car_fields = ['model', 'kilometer', 'model_year', 'brand', 'fuel_type', 'transmission']
            for field in required_car_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError({field: f"This field is required for car offers."})
        elif offer_type == 'property':
            required_property_fields = ['address', 'build_date', 'square_meter', 'room_type', 'document_type']
            for field in required_property_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError({field: f"This field is required for property offers."})
        return attrs

    def create(self, validated_data):
        car_fields = ['model', 'kilometer', 'model_year', 'brand', 'fuel_type', 'transmission']
        property_fields = ['address', 'build_date', 'square_meter', 'room_type', 'document_type']
        images = validated_data.pop('images', [])

        car_data = {f: validated_data.pop(f) for f in car_fields if f in validated_data}
        property_data = {f: validated_data.pop(f) for f in property_fields if f in validated_data}

        offer = Offer.objects.create(**validated_data)

        if offer.offer_type == 'car' and car_data:
            CarOffer.objects.create(offer=offer, **car_data)
        elif offer.offer_type == 'property' and property_data:
            PropertyOffer.objects.create(offer=offer, **property_data)

        for image_file in images:
            OfferImage.objects.create(offer=offer, image=image_file)

        return offer

class UserOfferAdminSerializer(serializers.ModelSerializer):
    images = OfferImageSerializer(many=True, read_only=True)
    responses = OfferResponseSerializer(many=True, read_only=True)

    car_details = CarOfferDetailsSerializer(required=False, allow_null=True)
    property_details = PropertyOfferDetailsSerializer(required=False, allow_null=True)

    class Meta:
        model = Offer
        fields = [
            'id', 'full_name', 'email', 'phone', 'details',
            'offer_type', 'city', 'area', 'price',
            'is_active', 'created_at', 'updated_at',
            'images',
            'car_details',
            'property_details',
            'responses'
        ]

    def update(self, instance, validated_data):
        car_data = validated_data.pop('car_details', None)
        property_data = validated_data.pop('property_details', None)

        instance = super().update(instance, validated_data)

        if instance.offer_type == 'car' and car_data is not None:
            car_offer_instance, created = CarOffer.objects.update_or_create(
                offer=instance, defaults=car_data
            )
        elif instance.offer_type != 'car' and hasattr(instance, 'car_details'):
            instance.car_details.delete()

        if instance.offer_type == 'property' and property_data is not None:
            property_offer_instance, created = PropertyOffer.objects.update_or_create(
                offer=instance, defaults=property_data
            )
        elif instance.offer_type != 'property' and hasattr(instance, 'property_details'):
            instance.property_details.delete()

        return instance

    def to_representation(self, instance):
        """
        Clean up representation to only include relevant details sub-object.
        """
        ret = super().to_representation(instance)
        if instance.offer_type == 'car':
            if 'property_details' in ret:
                del ret['property_details']
        elif instance.offer_type == 'property':
            if 'car_details' in ret:
                del ret['car_details']
        else:
            if 'property_details' in ret: del ret['property_details']
            if 'car_details' in ret: del ret['car_details']
        return ret


