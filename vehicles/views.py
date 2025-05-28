
from django.db import models
from django.db import transaction
from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from knox.auth import TokenAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from properties.constants import PREDEFINED_CAR_DATA
from .filters import CarFilter
from .models import (
    CarAdvertisement, CarImage,CarExternalFeature, CarInternalFeature
)
from .serializers import (
    CarAdminListSerializer, CarDetailSerializer, CarAdminCreateUpdateSerializer,
    CarListSerializer, CarImageSerializer, CarBasicSerializer
)
from properties.utils import base64_to_image_file
from .utils import get_model_form_schema

class CarAdminViewSet(viewsets.ModelViewSet):
    """ViewSet for Admin users to manage Car Advertisements."""
    queryset = CarAdvertisement.objects.select_related( 'user', 'explanation', 'external_features', 'internal_features'
    ).prefetch_related('images').all()
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    parser_classes = [FormParser, JSONParser]
    filterset_class = CarFilter
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'brand', 'series', 'explanation__explanation']
    ordering_fields = ['created_at', 'published_date', 'price', 'title', 'model_year']
    ordering = ['-created_at']

    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'list':
            return CarAdminListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CarAdminCreateUpdateSerializer
        return CarDetailSerializer

    def get_queryset(self):
        queryset = CarAdvertisement.objects.filter(is_active=True).select_related('user', 'explanation', 'external_features', 'internal_features').prefetch_related('images')
        return queryset


    @transaction.atomic
    def create(self, request, *args, **kwargs):
        mutable_request_data = request.data.copy()
        images_payload_list = mutable_request_data.pop('images', None)

        if images_payload_list is not None and not isinstance(images_payload_list, list):
            return Response(
                {"detail": "The 'images_payload' field must be a list of image objects."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=mutable_request_data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(user=self.request.user)

        has_explicit_cover_in_payload = any(
            img_data.get('is_cover') for img_data in images_payload_list if isinstance(img_data, dict))
        cover_image_assigned_in_loop = False

        if images_payload_list:
            for i, image_data_item in enumerate(images_payload_list):
                if not isinstance(image_data_item, dict):
                    continue

                base64_str = image_data_item.get('image')
                is_explicitly_cover = image_data_item.get('is_cover', False)
                image_content_file = base64_to_image_file(base64_str, name_prefix=f"car_{instance.id}_img_")

                if image_content_file:
                    current_image_is_cover = False
                    if has_explicit_cover_in_payload:
                        if is_explicitly_cover and not cover_image_assigned_in_loop:
                            current_image_is_cover = True
                            cover_image_assigned_in_loop = True
                    elif not cover_image_assigned_in_loop and i == 0:
                        current_image_is_cover = True
                        cover_image_assigned_in_loop = True

                    CarImage.objects.create(
                        car_ad=instance,
                        image=image_content_file,
                        is_cover=current_image_is_cover
                    )

        if not CarImage.objects.filter(car_ad=instance, is_cover=True).exists():
            first_available_image = CarImage.objects.filter(car_ad=instance).order_by('uploaded_at').first()
            if first_available_image:
                first_available_image.is_cover = True
                first_available_image.save(update_fields=['is_cover'])

        instance.refresh_from_db()
        detail_serializer = CarDetailSerializer(instance, context=self.get_serializer_context())
        headers = self.get_success_headers(detail_serializer.data)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        mutable_request_data = request.data.copy()
        images_payload_list = mutable_request_data.pop('images', None) 

        if images_payload_list is not None:
             if not isinstance(images_payload_list, list):
                return Response(
                    {"detail": "If 'images_payload' is provided for update, it must be a list of image objects."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        serializer = self.get_serializer(instance, data=mutable_request_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        updated_instance = serializer.save()
        if images_payload_list is not None: 
            existing_images = CarImage.objects.filter(car_ad=updated_instance)
            for img in existing_images:
                img.delete()
            
            created_image_count = 0
            has_explicit_cover_in_payload = any(img_data.get('is_cover') for img_data in images_payload_list if isinstance(img_data, dict))
            cover_image_assigned_in_loop = False

            if images_payload_list: 
                for i, image_data_item in enumerate(images_payload_list):
                    if not isinstance(image_data_item, dict):
                        continue

                    base64_str = image_data_item.get('image')
                    is_explicitly_cover = image_data_item.get('is_cover', False)
                    
                    if not base64_str:
                        continue

                    image_content_file = base64_to_image_file(base64_str, name_prefix=f"car_{updated_instance.id}_img_")
                    
                    if image_content_file:
                        current_image_is_cover = False
                        if has_explicit_cover_in_payload:
                            if is_explicitly_cover and not cover_image_assigned_in_loop:
                                current_image_is_cover = True
                                cover_image_assigned_in_loop = True
                        elif not cover_image_assigned_in_loop and i == 0: 
                            current_image_is_cover = True
                            cover_image_assigned_in_loop = True
                        
                        CarImage.objects.create(
                            car_ad=updated_instance,
                            image=image_content_file,
                            is_cover=current_image_is_cover
                        )
                        created_image_count += 1
                        
                if not CarImage.objects.filter(car_ad=updated_instance, is_cover=True).exists():
                    first_available_image = CarImage.objects.filter(car_ad=updated_instance).order_by('uploaded_at').first()
                    if first_available_image:
                        first_available_image.is_cover = True
                        first_available_image.save(update_fields=['is_cover'])

        updated_instance.refresh_from_db()
        detail_serializer = CarDetailSerializer(updated_instance, context=self.get_serializer_context())
        return Response(detail_serializer.data)

    @action(detail=True, methods=['post'], parser_classes=[JSONParser], url_path='upload-images')
    def upload_images(self, request, pk=None):
        car_ad = self.get_object()
        images_payload_list = request.data.get('images')
        if not images_payload_list or not isinstance(images_payload_list, list):
            return Response(
                {"detail": "'images_payload' field is missing, empty, or not a list of image objects."},
                status=status.HTTP_400_BAD_REQUEST
            )
        created_images = []
        ad_already_has_cover = CarImage.objects.filter(car_ad=car_ad, is_cover=True).exists()
        cover_assigned_in_this_batch = False

        for i, image_data_item in enumerate(images_payload_list):
            if not isinstance(image_data_item, dict):
                continue
            base64_str = image_data_item.get('image')
            is_explicitly_cover_from_payload = image_data_item.get('is_cover', False)

            image_content_file = base64_to_image_file(base64_str, name_prefix=f"car_{car_ad.id}_upload_")

            if image_content_file:
                current_image_is_cover = False
                if not ad_already_has_cover and not cover_assigned_in_this_batch:
                    if is_explicitly_cover_from_payload:
                        current_image_is_cover = True
                        cover_assigned_in_this_batch = True
                        if current_image_is_cover:
                            CarImage.objects.filter(car_ad=car_ad, is_cover=True).update(is_cover=False)
                    elif i == 0:
                        current_image_is_cover = True
                        cover_assigned_in_this_batch = True
                elif ad_already_has_cover and is_explicitly_cover_from_payload and not cover_assigned_in_this_batch:
                    CarImage.objects.filter(car_ad=car_ad, is_cover=True).update(is_cover=False)
                    current_image_is_cover = True
                    cover_assigned_in_this_batch = True

            img = CarImage.objects.create(
                        car_ad=car_ad,
                        image=image_content_file,
                        is_cover=current_image_is_cover
                    )
            created_images.append(img)
            if current_image_is_cover:
                ad_already_has_cover = True
        serializer = CarImageSerializer(created_images, many=True, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='set-cover-image/(?P<image_pk>[^/.]+)')
    def set_cover_image(self, request, pk=None, image_pk=None):
        car_ad = self.get_object()
        try: image_to_set = CarImage.objects.get(pk=image_pk, car_ad=car_ad)
        except CarImage.DoesNotExist: return Response({"detail": "Image not found for this car."}, status=status.HTTP_404_NOT_FOUND)
        with transaction.atomic():
            CarImage.objects.filter(car_ad=car_ad, is_cover=True).update(is_cover=False)
            image_to_set.is_cover = True
            image_to_set.save(update_fields=['is_cover'])
        serializer = CarImageSerializer(image_to_set, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'], url_path='delete-image/(?P<image_pk>[^/.]+)')
    def delete_image(self, request, pk=None, image_pk=None):
        car_ad = self.get_object()
        try: image_to_delete = CarImage.objects.get(pk=image_pk, car_ad=car_ad)
        except CarImage.DoesNotExist: return Response({"detail": "Image not found for this car."}, status=status.HTTP_404_NOT_FOUND)
        was_cover = image_to_delete.is_cover
        image_to_delete.delete()
        if was_cover:
             new_cover = CarImage.objects.filter(car_ad=car_ad).first()
             if new_cover:
                 new_cover.is_cover = True
                 new_cover.save(update_fields=['is_cover'])
        return Response(status=status.HTTP_204_NO_CONTENT)

class CarBasicListView(generics.ListAPIView):
    serializer_class = CarBasicSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CarAdvertisement.objects.filter(is_active=True).prefetch_related('images').order_by('-published_date')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['title']
    ordering_fields = ['published_date', 'price', 'title']

class PublicCarListView(generics.ListAPIView):
    serializer_class = CarListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CarFilter
    search_fields = ['title', 'brand', 'series', 'explanation__explanation']
    ordering_fields = ['published_date', 'price', 'title', 'model_year']
    ordering = ['-published_date']

    def get_queryset(self):
        return CarAdvertisement.objects.filter(is_active=True).prefetch_related('images').order_by('-published_date')

class PublicCarDetailView(generics.RetrieveAPIView):
    serializer_class = CarDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        return CarAdvertisement.objects.filter(is_active=True).select_related('user', 'explanation', 'external_features', 'internal_features').prefetch_related('images')

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

class CarExternalFeaturesMetadataView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        external_features = get_feature_metadata(CarExternalFeature)
        return Response(external_features)

class CarInternalFeaturesMetadataView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        internal_features = get_feature_metadata(CarInternalFeature)
        return Response(internal_features)

class CarAdvertisementFormSchemaView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            main_model = CarAdvertisement
            form_meta = get_model_form_schema(main_model)

            response_data = {
                          "form_meta": form_meta,
                          "brand_series_map": PREDEFINED_CAR_DATA
            }
            return Response(response_data)
        except Exception as e:
            print(f"Error generating schema: {e}")
            import traceback
            traceback.print_exc()
            return Response({"error": "Could not generate form schema.", "details": str(e)}, status=500)