from django.db import transaction
from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from knox.auth import TokenAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from .models import PropertyAdvertisement, PropertyImage, Location
from .serializers import (
    PropertyAdminListSerializer, PropertyDetailSerializer, PropertyAdminCreateUpdateSerializer,
    PropertyListSerializer, PropertyImageSerializer
)
from .filters import PropertyFilter


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