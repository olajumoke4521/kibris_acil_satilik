from django.db import models
from django.db import transaction
from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from knox.auth import TokenAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from .filters import CarFilter
from .models import (
    CarAdvertisement, CarImage,CarExternalFeature, CarInternalFeature
)
from .serializers import (
    CarAdminListSerializer, CarDetailSerializer, CarAdminCreateUpdateSerializer,
    CarListSerializer, CarImageSerializer
)


class CarAdminViewSet(viewsets.ModelViewSet):
    """ViewSet for Admin users to manage Car Advertisements."""
    queryset = CarAdvertisement.objects.select_related( 'user', 'explanation', 'external_features', 'internal_features'
    ).prefetch_related('images').all()
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        instance = serializer.save(user=self.request.user)

        images_data = request.FILES.getlist('images')
        if images_data:
            make_first_cover = not CarImage.objects.filter(car_ad=instance, is_cover=True).exists()
            for i, image_file in enumerate(images_data):
                CarImage.objects.create(
                    car_ad=instance,
                    image=image_file,
                    is_cover=(i == 0 and make_first_cover)
                )

        detail_serializer = CarDetailSerializer(instance, context=self.get_serializer_context())
        headers = self.get_success_headers(detail_serializer.data)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        updated_instance = serializer.save()

        detail_serializer = CarDetailSerializer(updated_instance, context=self.get_serializer_context())
        return Response(detail_serializer.data)

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser], url_path='upload-images')
    def upload_images(self, request, pk=None):
        car_ad = self.get_object()
        images_data = request.FILES.getlist('images')
        if not images_data: return Response({"detail": "No images provided."}, status=status.HTTP_400_BAD_REQUEST)
        make_first_cover = not CarImage.objects.filter(car_ad=car_ad, is_cover=True).exists()
        created_images = []
        for i, image_file in enumerate(images_data):
            is_cover_candidate = (i == 0 and make_first_cover and not car_ad.images.exists())
            img = CarImage.objects.create(car_ad=car_ad, image=image_file, is_cover=is_cover_candidate)
            created_images.append(img)
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