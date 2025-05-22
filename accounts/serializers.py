from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomerOffer, OfferImage
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


class OfferImageSerializer(serializers.ModelSerializer):
    """Serializer for OfferImage objects"""
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = OfferImage
        fields = ('id', 'image', 'image_url', 'uploaded_at')
        read_only_fields = ('id', 'image_url', 'uploaded_at')

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class CustomerOfferSerializer(serializers.ModelSerializer):
    """Serializer for CustomerOffer objects"""
    images = OfferImageSerializer(many=True, read_only=True)

    class Meta:
        model = CustomerOffer
        fields = (
            'id', 'name', 'address', 'unit_number', 'city', 'state',
            'room_type', 'price', 'description', 'email', 'phone',
            'status', 'images', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'images')


class CustomerOfferCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating CustomerOffer objects (Public)"""

    class Meta:
        model = CustomerOffer
        fields = (
            'name', 'address', 'unit_number', 'city', 'state',
            'room_type', 'price', 'description', 'email', 'phone',
        )


    def validate(self, attrs):
        """Ensure at least email or phone is provided"""
        email = attrs.get('email')
        phone = attrs.get('phone')

        if not email and not phone:
            raise serializers.ValidationError(
                "Please provide either an email address or a phone number so we can contact you."
            )
        return attrs