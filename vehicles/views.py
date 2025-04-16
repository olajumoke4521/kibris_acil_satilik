from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from knox.auth import TokenAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    CarAdvertisement, CarImage, CarExplanation,
    CarExternalFeature, CarInternalFeature
)
from accounts.models import Customer
from .serializers import (
    CarAdminListSerializer, CarDetailSerializer, CarAdminCreateUpdateSerializer,
    CarListSerializer, CarImageSerializer
)


class CarAdminViewSet(viewsets.ModelViewSet):
    """ViewSet for Admin users to manage Car Advertisements."""
    queryset = CarAdvertisement.objects.select_related('customer', 'user', 'explanation', 'external_features', 'internal_features'
    ).prefetch_related('images').all()
    permission_classes = [permissions.IsAdminUser]
    authentication_classes = [TokenAuthentication]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'advertise_no', 'brand', 'model', 'explanation__explanation', 'customer__name']
    ordering_fields = ['created_at', 'published_date', 'price', 'title', 'model_year', 'mileage']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return CarAdminListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CarAdminCreateUpdateSerializer
        return CarDetailSerializer

    def _update_or_create_nested(self, instance, model_class, related_name_prefix, data):
         """Helper: Updates or creates OneToOne related objects for cars."""
         if data is not None:
             obj, created = model_class.objects.update_or_create(
                 car_ad=instance,
                 defaults=data
             )
             return obj
         return None


    @transaction.atomic
    def perform_create(self, serializer):
        """Creation of car ad and related objects."""
        admin_user = self.request.user
        validated_data = serializer.validated_data.copy()

        explanation_data = validated_data.pop('explanation', None)
        external_features_data = validated_data.pop('external_features', None)
        internal_features_data = validated_data.pop('internal_features', None)

        instance = serializer.save(user=admin_user)

        if explanation_data:
            CarExplanation.objects.create(car_ad=instance, explanation=explanation_data)
        self._update_or_create_nested(instance, CarExternalFeature, 'external_features', external_features_data)
        self._update_or_create_nested(instance, CarInternalFeature, 'internal_features', internal_features_data)

        return instance

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)

        images_data = request.FILES.getlist('images')
        if images_data:
            make_first_cover = not CarImage.objects.filter(car_ad=instance, is_cover=True).exists()
            for i, image_file in enumerate(images_data):
                CarImage.objects.create(
                    car_ad=instance, image=image_file,
                    is_cover=(i == 0 and make_first_cover)
                )

        detail_serializer = CarDetailSerializer(instance, context=self.get_serializer_context())
        headers = self.get_success_headers(detail_serializer.data)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


    @transaction.atomic
    def perform_update(self, serializer):
        """Update of car ad and related objects."""
        instance = serializer.instance
        validated_data = serializer.validated_data.copy()

        explanation_data = validated_data.pop('explanation', None)
        external_features_data = validated_data.pop('external_features', None)
        internal_features_data = validated_data.pop('internal_features', None)

        instance = serializer.save()

        if explanation_data is not None:
            CarExplanation.objects.update_or_create(car_ad=instance, defaults={'explanation': explanation_data})
        self._update_or_create_nested(instance, CarExternalFeature, 'external_features', external_features_data)
        self._update_or_create_nested(instance, CarInternalFeature, 'internal_features', internal_features_data)

        return instance

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        detail_serializer = CarDetailSerializer(instance, context=self.get_serializer_context())
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
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'brand', 'model', 'explanation__explanation']
    ordering_fields = ['published_date', 'price', 'title', 'model_year']
    ordering = ['-published_date']

    def get_queryset(self):
        return CarAdvertisement.objects.filter(
            advertise_status='on'
        ).prefetch_related(
            'images'
        ).order_by('-published_date')


class PublicCarDetailView(generics.RetrieveAPIView):
    serializer_class = CarDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'

    def get_queryset(self):
        return CarAdvertisement.objects.filter(
            advertise_status='on'
        ).select_related(
            'customer', 'user', 'explanation', 'external_features', 'internal_features'
        ).prefetch_related(
            'images'
        )