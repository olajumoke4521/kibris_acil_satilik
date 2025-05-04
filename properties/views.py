import json
import uuid

from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from knox.auth import TokenAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from .models import PropertyAdvertisement, PropertyImage, Location, PropertyInteriorFeature, PropertyExternalFeature
from accounts.models import Customer
from .serializers import (
    PropertyAdminListSerializer, PropertyDetailSerializer, PropertyAdminCreateUpdateSerializer,
    PropertyListSerializer, PropertyImageSerializer
)
from accounts.serializers import CustomerSerializer
from .filters import PropertyFilter
from django.db import models



class PropertyAdminViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Admin users to manage Property Advertisements.
    Handles CRUD, image uploads, and feature updates.
    """
    queryset = PropertyAdvertisement.objects.select_related(
        'location', 'user', 'explanation', 'external_features', 'interior_features'
    ).prefetch_related('images').all()
    permission_classes = [permissions.IsAdminUser]
    authentication_classes = [TokenAuthentication]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PropertyFilter
    search_fields = ['title', 'advertise_no', 'explanation__explanation', 'location__city', 'location__district']
    ordering_fields = ['created_at', 'published_date', 'price', 'title']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return PropertyAdminListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PropertyAdminCreateUpdateSerializer
        return PropertyDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset

    def get_or_create_location(self, validated_data):
        province = validated_data.pop('province', None)
        district = validated_data.pop('district', None)
        neighborhood = validated_data.pop('neighborhood', None)

        if not province: return None

        location_obj, _ = Location.objects.get_or_create(
            province=province,
            district=district if district else None,
            neighborhood=neighborhood if neighborhood else None
        )
        return location_obj

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        location_obj = self.get_or_create_location({
            'province': data.get('province'),
            'district': data.get('district'),
            'neighborhood': data.get('neighborhood')
        })

        instance = serializer.save(user=self.request.user, location=location_obj)

        images_data = request.FILES.getlist('images')
        if images_data:
            make_first_cover = not PropertyImage.objects.filter(property_ad=instance, is_cover=True).exists()
            for i, image_file in enumerate(images_data):
                PropertyImage.objects.create(
                    property_ad=instance,
                    image=image_file,
                    is_cover=(i == 0 and make_first_cover)
                )

        detail_serializer = PropertyDetailSerializer(instance, context=self.get_serializer_context())
        headers = self.get_success_headers(detail_serializer.data)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()

        if 'province' in data:
            location_obj = self.get_or_create_location({
                'province': data.get('province'),
                'district': data.get('district'),
                'neighborhood': data.get('neighborhood')
            })

            location = location_obj
        else:
            location = instance.location

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save(location=location)

        detail_serializer = PropertyDetailSerializer(updated_instance, context=self.get_serializer_context())
        return Response(detail_serializer.data)

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser], url_path='upload-images')
    def upload_images(self, request, pk=None):
        """Upload additional images for a specific property."""
        property_ad = self.get_object()
        images_data = request.FILES.getlist('images')
        if not images_data:
            return Response({"detail": "No images provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if a cover photo already exists
        make_first_cover = not PropertyImage.objects.filter(property_ad=property_ad, is_cover=True).exists()

        created_images = []
        for i, image_file in enumerate(images_data):
            # Check if it's the very first image being uploaded for this property ever
            is_cover_candidate = (i == 0 and make_first_cover and not property_ad.images.exists())
            img = PropertyImage.objects.create(
                property_ad=property_ad,
                image=image_file,
                is_cover=is_cover_candidate
            )
            created_images.append(img)

        serializer = PropertyImageSerializer(created_images, many=True, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='set-cover-image/(?P<image_pk>[^/.]+)')
    def set_cover_image(self, request, pk=None, image_pk=None):
        """Set a specific image as the cover photo."""
        property_ad = self.get_object()
        try:
            image_to_set = PropertyImage.objects.get(pk=image_pk, property_ad=property_ad)
        except PropertyImage.DoesNotExist:
            return Response({"detail": "Image not found for this property."}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            PropertyImage.objects.filter(property_ad=property_ad, is_cover=True).update(is_cover=False)
            image_to_set.is_cover = True
            image_to_set.save(update_fields=['is_cover'])

        serializer = PropertyImageSerializer(image_to_set, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'], url_path='delete-image/(?P<image_pk>[^/.]+)')
    def delete_image(self, request, pk=None, image_pk=None):
        """Delete a specific image."""
        property_ad = self.get_object()
        try:
            image_to_delete = PropertyImage.objects.get(pk=image_pk, property_ad=property_ad)
        except PropertyImage.DoesNotExist:
            return Response({"detail": "Image not found for this property."}, status=status.HTTP_404_NOT_FOUND)
        was_cover = image_to_delete.is_cover
        image_to_delete.delete()

        if was_cover:
             new_cover = PropertyImage.objects.filter(property_ad=property_ad).first()
             if new_cover:
                 new_cover.is_cover = True
                 new_cover.save(update_fields=['is_cover'])

        return Response(status=status.HTTP_204_NO_CONTENT)

class CreateCustomerAndPropertyView(APIView):
    """
    Handles the creation of a Customer and a related PropertyAdvertisement
    (including Location, Features, Explanation, Images) in a single, atomic request.
    """
    permission_classes = [permissions.IsAdminUser] # Or other appropriate permission
    authentication_classes = [TokenAuthentication]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_or_create_location(self, data):
        province = data.get('province', None)
        district = data.get('district', None)
        neighborhood = data.get('neighborhood', None)

        if not province: return None
        district = district if district else None
        neighborhood = neighborhood if neighborhood else None

        location_obj, created = Location.objects.get_or_create(
            province=province,
            district=district,
            neighborhood=neighborhood
        )
        return location_obj

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        Handles the POST request to create both Customer and PropertyAdvertisement.
        """
        data = request.data.copy()
        customer_instance = None
        property_instance = None

        customer_data = {}
        property_data = {}
        customer_photo_file = None
        property_image_files = request.FILES.getlist('images')

        customer_field_keys = ['name', 'email', 'photo', 'mobile_number', 'mobile_number_2', 'mobile_number_3',
                               'telephone', 'telephone_2',
                               'telephone_3', 'fax', 'type_of_advertise', 'customer_role']
        customer_unique_key = 'email'
        nested_property_keys = ['external_features', 'interior_features']
        location_field_keys = ['province', 'district', 'neighborhood']

        for key, value in request.data.items():
            if key == 'photo' and value:
                if hasattr(value, 'content_type') and 'image' in value.content_type:
                    customer_photo_file = value
                else:
                    print(f"Warning: Ignoring non-image file provided for 'photo': {key}")
                continue

            if key in customer_field_keys:
                customer_data[key] = value
            elif key not in ['images']:
                if key in nested_property_keys and isinstance(value, str):
                    try:
                        property_data[key] = json.loads(value)
                    except json.JSONDecodeError:
                        return Response({key: [f"Invalid JSON string provided for {key}."]},
                                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    property_data[key] = value

        lookup_value = customer_data.get(customer_unique_key)
        if not lookup_value:
            return Response({customer_unique_key: ["This field is required to find or create a customer."]},
                            status=status.HTTP_400_BAD_REQUEST)

        defaults_for_create = {}
        # Define which customer keys expect a single value
        single_value_customer_keys = ['name', 'mobile_number', 'mobile_number_2', 'mobile_number_3', 'telephone',
                                      'telephone_2',
                                      'telephone_3', 'fax', 'type_of_advertise', 'customer_role']

        for key, value in customer_data.items():
            if key != customer_unique_key and key != 'photo':
                if key in single_value_customer_keys and isinstance(value, list):
                    if value:
                        print(f"Warning: Received list for customer key '{key}'. Using first element: '{value[0]}'")
                        value = value[0]
                    else:
                        print(f"Warning: Received empty list for customer key '{key}'. Skipping.")
                        continue
                defaults_for_create[key] = value

        try:
            customer_instance, created = Customer.objects.get_or_create(
                **{customer_unique_key: lookup_value},
                defaults=defaults_for_create
            )

            save_customer_needed = False
            if created and hasattr(customer_instance, 'user') and not customer_instance.user:
                customer_instance.user = request.user
                save_customer_needed = True

            if customer_photo_file:
                customer_instance.photo = customer_photo_file
                save_customer_needed = True

            if save_customer_needed:
                customer_instance.save()

        except IntegrityError as e:
            return Response({"customer_error": f"Database constraint issue during customer get/create: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({"customer_error": e.message_dict}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"customer_error": f"Failed to get or create customer: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST)


        location_instance = self.get_or_create_location(property_data)
        if location_instance is None and request.data.get('province'):
            return Response({"location_error": "Failed to get or create location based on provided province."},
                            status=status.HTTP_400_BAD_REQUEST)

        property_serializer = PropertyAdminCreateUpdateSerializer(data=property_data, context={'request': request})

        if not property_serializer.is_valid():
            return Response({"property_errors": property_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            property_instance = property_serializer.save(
                user=request.user,
                customer=customer_instance,
                location=location_instance
            )
        except ValidationError as e:
            return Response({"property_errors": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"property_errors": f"Failed to save property advertisement: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST)

        if property_image_files:
            make_first_cover = not PropertyImage.objects.filter(property_ad=property_instance, is_cover=True).exists()
            for i, image_file in enumerate(property_image_files):
                try:
                    PropertyImage.objects.create(
                        property_ad=property_instance,
                        image=image_file,
                        is_cover=(i == 0 and make_first_cover)
                    )
                except Exception as e:
                    print(f"Error saving property image {i}: {e}")
                    return Response({"image_error": f"Failed to save property image {i + 1}: {str(e)}"},
                                    status=status.HTTP_400_BAD_REQUEST)

        detail_serializer = PropertyDetailSerializer(property_instance, context={'request': request})
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

class PublicPropertyListView(generics.ListAPIView):
    """View for listing ACTIVE properties publicly"""
    serializer_class = PropertyListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PropertyFilter
    search_fields = ['title', 'explanation__explanation', 'location__city', 'location__district']
    ordering_fields = ['published_date', 'price', 'title']
    ordering = ['-published_date']

    def get_queryset(self):
        """Return active, published property advertisements"""
        return PropertyAdvertisement.objects.filter(advertise_status='on').select_related('location').prefetch_related('images').order_by('-published_date')


class PublicPropertyDetailView(generics.RetrieveAPIView):
    """View for retrieving ACTIVE property details publicly"""
    serializer_class = PropertyDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'

    def get_queryset(self):
        """Return active, published property advertisements"""
        return PropertyAdvertisement.objects.filter(advertise_status='on').select_related('location', 'customer', 'user', 'explanation', 'external_features', 'interior_features').prefetch_related('images')


def get_feature_metadata(model_class):
    feature_list = []
    for field in model_class._meta.get_fields():
        if isinstance(field, models.BooleanField):
            if field.verbose_name:
                base_label = field.verbose_name
            else:
                base_label = field.name.replace('_', ' ')

            final_label = base_label.title()

            feature_list.append({
                "key": field.name,
                "label": final_label
            })
    return feature_list

class PropertyExternalFeaturesMetadataView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        external_features = get_feature_metadata(PropertyExternalFeature)
        return Response(external_features)

class PropertyInteriorFeaturesMetadataView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        interior_features = get_feature_metadata(PropertyInteriorFeature)
        return Response(interior_features)