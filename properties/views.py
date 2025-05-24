import json
import os
import datetime
from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import validate_email
from django.db import transaction, IntegrityError
from django.db import models
from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from knox.auth import TokenAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from .models import PropertyAdvertisement, PropertyImage, Location, PropertyInteriorFeature, PropertyExternalFeature
from .serializers import (
    PropertyAdminListSerializer, PropertyDetailSerializer, PropertyAdminCreateUpdateSerializer,
    PropertyListSerializer, PropertyImageSerializer, LatestAdvertisementSerializer, PropertyBasicSerializer
)
from .filters import PropertyFilter
from vehicles.models import CarAdvertisement
from .constants import PREDEFINED_CAR_DATA, PROPERTY_TYPE_TR_LABELS_MAP, VEHICLE_TYPE_TR_LABELS_MAP, LOCATION_JSON_FILE_PATH
from .utils import get_dynamic_model_form_schema
from .data_loaders import CITY_AREAS_DATA




class PropertyAdminViewSet(viewsets.ModelViewSet):

    queryset = PropertyAdvertisement.objects.select_related(
        'location', 'user', 'explanation', 'external_features', 'interior_features'
    ).prefetch_related('images').all()
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PropertyFilter
    search_fields = ['title', 'advertise_no', 'explanation__explanation', 'location__city', 'location__area']
    ordering_fields = ['created_at', 'published_date', 'price', 'title']
    ordering = ['-created_at']

    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'list':
            return PropertyAdminListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PropertyAdminCreateUpdateSerializer
        return PropertyDetailSerializer

    def get_queryset(self):
        queryset = PropertyAdvertisement.objects.filter(is_active=True).select_related('location').prefetch_related('images').order_by('-published_date')
        return queryset

    def get_or_create_location(self, validated_data):
        city = validated_data.pop('city', None)
        area = validated_data.pop('area', None)

        if not city: return None

        location_obj, _ = Location.objects.get_or_create(
            city=city,
            area=area if area else None,
        )
        return location_obj

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        location_obj = self.get_or_create_location({
            'city': data.get('city'),
            'area': data.get('area'),
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

        if 'city' in data:
            location_obj = self.get_or_create_location({
                'city': data.get('city'),
                'area': data.get('area'),
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

class PropertyBasicListView(generics.ListAPIView):
    serializer_class = PropertyBasicSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PropertyAdvertisement.objects.filter(is_active=True).prefetch_related('images').order_by('-published_date')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['title']
    ordering_fields = ['published_date', 'price', 'title']
class PublicPropertyListView(generics.ListAPIView):
    """View for listing ACTIVE properties publicly"""
    serializer_class = PropertyListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PropertyFilter
    search_fields = ['title', 'explanation__explanation', 'location__city', 'location__area']
    ordering_fields = ['published_date', 'price', 'title']
    ordering = ['-published_date']

    def get_queryset(self):
        """Return active, published property advertisements"""
        return PropertyAdvertisement.objects.filter(is_active=True).select_related('location').prefetch_related('images').order_by('-published_date')


class PublicPropertyDetailView(generics.RetrieveAPIView):
    """View for retrieving ACTIVE property details publicly"""
    serializer_class = PropertyDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        """Return active, published property advertisements"""
        return PropertyAdvertisement.objects.filter(is_active=True).select_related('location', 'user', 'explanation', 'external_features', 'interior_features').prefetch_related('images')


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

class LatestAdvertisementsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    AD_COUNT_LIMIT =6

    def get(self, request, *args, **kwargs):
        latest_properties_qs = PropertyAdvertisement.objects.filter(
            is_active=True
        ).select_related(
            'location'
        ).prefetch_related(
            'images'
        ).order_by('-published_date')[:self.AD_COUNT_LIMIT]

        latest_cars_qs = CarAdvertisement.objects.filter(
            is_active=True
        ).prefetch_related(
            'images'
        ).order_by('-published_date')[:self.AD_COUNT_LIMIT]

        combined_ads_list = list(latest_properties_qs) + list(latest_cars_qs)

        combined_ads_list.sort(key=lambda ad: ad.published_date, reverse=True)

        final_latest_ads_to_serialize = combined_ads_list[:self.AD_COUNT_LIMIT]

        serializer = LatestAdvertisementSerializer(
            final_latest_ads_to_serialize,
            many=True,
            context={'request': request}
        )

        return Response(serializer.data)


def get_choices_as_list_of_dicts(choices_tuple):
    """Helper function to convert Django choices tuple to a list of dicts."""
    return [{"value": choice[0], "label": choice[1]} for choice in choices_tuple]


def get_bilingual_choices_as_list_of_dicts(choices_tuple, tr_label_map=None, en_label_map=None):
    bilingual_list = []
    for value, default_label in choices_tuple:
        if tr_label_map and isinstance(tr_label_map, dict) and value in tr_label_map:
            label_tr = tr_label_map[value]
        else:
            label_tr = default_label

        if en_label_map and isinstance(en_label_map, dict) and value in en_label_map:
            label_en = en_label_map[value]
        else:
            label_en = default_label

        bilingual_list.append({
            "value": value,
            "label_tr": label_tr,
            "label_en": label_en
        })
    return bilingual_list

class CombinedFilterOptionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def load_location_data_from_json(self):
        try:
            with open(LOCATION_JSON_FILE_PATH, 'r', encoding='utf-8') as f:
                raw_locations = json.load(f)
        except FileNotFoundError:
            print(f"ERROR: Location JSON file not found at {LOCATION_JSON_FILE_PATH}")
            return []
        except json.JSONDecodeError:
            print(f"ERROR: Could not decode JSON from {LOCATION_JSON_FILE_PATH}")
            return []

        grouped_by_province_value = {}

        for loc in raw_locations:
            province_val = loc.get("province_value")
            province_l_tr = loc.get("province_label_tr")
            province_l_en = loc.get("province_label_en")
            district_name = loc.get("district")

            if not province_val or not district_name:
                continue

            if province_val not in grouped_by_province_value:
                grouped_by_province_value[province_val] = {
                    "city": {
                        "value": province_val,
                        "label_tr": province_l_tr,
                        "label_en": province_l_en
                    },
                    "areas_temp_list": []
                }

            district_filter_value = district_name.lower().replace(" ", "-").replace("(", "").replace(")", "")
            area_object = {
                "value": district_filter_value,
                "label": district_name
            }

            grouped_by_province_value[province_val]["areas_temp_list"].append(area_object)

        final_city_areas_data = []
        for province_value_key, city_data_group in grouped_by_province_value.items():
            unique_areas = []
            seen_area_values = set()
            sorted_areas = sorted(city_data_group["areas_temp_list"], key=lambda x: x['label'])

            for area in sorted_areas:
                if area["value"] not in seen_area_values:
                    unique_areas.append(area)
                    seen_area_values.add(area["value"])

            final_city_areas_data.append({
                "city": city_data_group["city"],
                "areas": unique_areas
            })

        final_city_areas_data.sort(key=lambda x: x['city']['label_tr'])

        return final_city_areas_data

    def get_property_options(self):
        property_types = get_bilingual_choices_as_list_of_dicts(
            choices_tuple=PropertyAdvertisement.PROPERTY_TYPE_CHOICES,
            tr_label_map=PROPERTY_TYPE_TR_LABELS_MAP
        )
        room_types = get_choices_as_list_of_dicts(PropertyAdvertisement.ROOM_TYPE_CHOICES)

        city_areas_data = self.load_location_data_from_json()

        return {
            "propertyTypes": property_types,
            "cityAreas": city_areas_data,
            "roomTypes": room_types,
        }

    def get_car_options(self):
        vehicle_types = get_bilingual_choices_as_list_of_dicts(
            choices_tuple=CarAdvertisement.VEHICLE_TYPE_CHOICES,
            tr_label_map=VEHICLE_TYPE_TR_LABELS_MAP
        )
        fuel_types = get_choices_as_list_of_dicts(
            choices_tuple=CarAdvertisement.FUEL_TYPE_CHOICES,
        )

        gear_types = get_choices_as_list_of_dicts(
            choices_tuple=CarAdvertisement.GEAR_TYPE_CHOICES,
        )

        predefined_brands_list = []
        for brand_name in PREDEFINED_CAR_DATA.keys():
            predefined_brands_list.append(
                {"value": brand_name.lower().replace("-", "").replace(" ", ""), "label": brand_name})
        predefined_brands_list.sort(key=lambda x: x['label'])

        brand_series_structure = []
        for brand_name, data in PREDEFINED_CAR_DATA.items():
            series_list = [{"value": s.lower().replace(" ", "-"), "label": s} for s in data.get("series", [])]
            series_list.sort(key=lambda x: x['label'])
            brand_series_structure.append({
                "brand": {"value": brand_name.lower().replace("-", "").replace(" ", ""), "label": brand_name},
                "series": series_list
            })
        brand_series_structure.sort(key=lambda x: x['brand']['label'])

        start_year = 2010
        end_year = datetime.date.today().year

        model_years_for_dropdown = []
        for year in range(end_year, start_year - 1, -1):
            year_str = str(year)
            model_years_for_dropdown.append({
                "value": year_str,
                "label": year_str
            })

        return {
            "vehicleTypes": vehicle_types,
            "fuelTypes": fuel_types,
            "transmissionTypes": gear_types,
            "modelYears": model_years_for_dropdown,
            "brandSeriesData": brand_series_structure,
        }

    def get(self, request, *args, **kwargs):
        data = {
            "property": self.get_property_options(),
            "car": self.get_car_options()
        }
        return Response(data)



class PropertyAdvertisementFormSchemaView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        main_model = PropertyAdvertisement
        app_label = main_model._meta.app_label


        property_special_handlers = {
            "location": {
                "type": "location_picker_new",
                "field_name_match": "location",
                "related_model_app": app_label,
                "related_model_name": "Location",
                "data_source_key": "cityAreas",
                "city_object_value_key": "value",
                "city_object_label_en_key": "label_en",
                "city_object_label_tr_key": "label_tr",
                "city_object_areas_list_key": "areas",
                "area_object_value_key": "value",
                "area_object_label_key": "label",
                "city_payload_key": "city",
                "area_payload_key": "area",
            }
        }

        property_nested_objects = {
            'external_features': 'PropertyExternalFeature',
            'interior_features': 'PropertyInteriorFeature',
        }
        property_list_children = {
            'images': 'PropertyImage',
        }
        property_single_field_one_to_one = {
            'explanation': ('PropertyExplanation', 'explanation'),
        }

        try:
            form_meta = get_dynamic_model_form_schema(
                main_model,
                app_label=app_label,
                nested_object_relations_config=property_nested_objects,
                list_child_relations_config=property_list_children,
                single_field_one_to_one_config=property_single_field_one_to_one,
                special_handlers=property_special_handlers
            )

            response_data = {
                "form_meta": form_meta,
                "cityAreas": CITY_AREAS_DATA,
            }
            return Response(response_data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": "Could not generate property form schema.", "details": str(e)}, status=500)
