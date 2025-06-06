from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, viewsets, filters as drf_filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import login
from django.db import IntegrityError
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView
from knox.auth import TokenAuthentication

from properties.models import PropertyAdvertisement
from vehicles.models import CarAdvertisement
from .filters import OfferFilter
from .models import User, OfferImage, Offer, OfferResponse
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer, OfferResponseSerializer, \
    UserOfferAdminSerializer, UserOfferCreateSerializer, OfferImageSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from collections import OrderedDict
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = self.perform_create(serializer)

            user.is_staff = True
            user.is_superuser = True
            user.save()

            _, token = AuthToken.objects.create(user)

            response_data = {
                "user": UserSerializer(user, context=self.get_serializer_context()).data,
                "token": token,
                "message": "User registered successfully"
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except IntegrityError:
            return Response(
                {"detail": "An account with the same email already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_create(self, serializer):
        return serializer.save()


class LoginView(KnoxLoginView):
    """View for user login using Knox authentication"""
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        login(request, user)

        response = super().post(request, format=format)

        response.data['user'] = UserSerializer(user).data

        return response


class UserDetailView(generics.RetrieveUpdateAPIView):
    """View for retrieving and updating user details"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)


# --- Admin ViewSet for Managing Offers ---
class OfferAdminViewSet(viewsets.ModelViewSet):
    serializer_class = UserOfferAdminSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = OfferFilter

    search_fields = [
        'full_name', 'email', 'phone', 'details', 'city', 'area', 'id',
        'car_details__model', 'car_details__brand',
        'property_details__address'
    ]
    ordering_fields = ['created_at', 'price', 'city', 'offer_type']
    def get_queryset(self):
        return Offer.objects.select_related(
            'car_details',
            'property_details'
        ).prefetch_related(
            'images',
            'responses__created_by',
            'responses__offered_by'
        ).filter(is_active=True).all().order_by('-created_at')

    @action(detail=True, methods=['post'], serializer_class=OfferResponseSerializer, url_path='respond')
    def create_admin_response(self, request, pk=None):
        offer_instance = self.get_object()
        serializer = OfferResponseSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(offer=offer_instance, created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], serializer_class=OfferResponseSerializer, url_path='responses')
    def list_admin_responses(self, request, pk=None):
        offer = self.get_object()
        responses = offer.responses.all().select_related('created_by', 'offered_by')
        serializer = OfferResponseSerializer(responses, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='images/(?P<image_pk>[^/.]+)/update',
            serializer_class=OfferImageSerializer)
    def update_offer_image_flags(self, request, pk=None, image_pk=None):
        offer = self.get_object()
        try:
            offer_image = OfferImage.objects.get(pk=image_pk, offer=offer)
        except OfferImage.DoesNotExist:
            return Response({"error": "Image not found for this offer."}, status=status.HTTP_404_NOT_FOUND)

        serializer = OfferImageSerializer(offer_image, data=request.data, partial=True,
                                                context={'request': request})
        if serializer.is_valid():
            serializer.save()
            full_image_serializer = OfferImageSerializer(offer_image, context={'request': request})
            return Response(full_image_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OfferResponseAdminViewSet(viewsets.ModelViewSet):
    queryset = OfferResponse.objects.select_related('offer', 'created_by', 'offered_by').filter(is_active=True).all()
    serializer_class = OfferResponseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by_user=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

class PublicOfferCreateView(generics.CreateAPIView):
    serializer_class = UserOfferCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": "Your offer request has been submitted. We will review it and contact you.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )

class DashboardTotalsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request, format=None):
        total_cars = CarAdvertisement.objects.filter(is_active=True).count()
        total_properties = PropertyAdvertisement.objects.filter(is_active=True).count()
        total_offers = Offer.objects.filter(is_active=True).count()

        data = {
            "cars": total_cars,
            "properties": total_properties,
            "offers": total_offers,
        }
        return Response(data)
class APIRootView(APIView):
    """
    API Root view providing links to major application endpoints.
    """
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        data = OrderedDict([
            # === Accounts Endpoints ===
            ('register', reverse('register', request=request, format=format)),
            ('login', reverse('login', request=request, format=format)),
            ('logout', reverse('logout', request=request, format=format)),
            ('user-detail', reverse('user-detail', request=request, format=format)),
            ('public-offer-create', reverse('public-offer-create', request=request, format=format)),
            ('admin-offers', reverse('admin-offer-list', request=request, format=format)),

            # === Properties Endpoints ===
            ('properties-public-list', reverse('public-property-list', request=request, format=format)),
            ('properties-admin-list', reverse('admin-property-list', request=request, format=format)),
            ('properties-features-external', reverse('property-external-features-metadata', request=request, format=format)),
            ('properties-features-interior', reverse('property-interior-features-metadata', request=request, format=format)),


            # === Vehicles Endpoints ===
             ('vehicles-public-list', reverse('public-car-list', request=request, format=format)),
             ('vehicles-admin-list', reverse('admin-car-list', request=request, format=format)),
             ('vehicles-features-external', reverse('car-external-features-metadata', request=request, format=format)),
             ('vehicles-features-internal', reverse('car-internal-features-metadata', request=request, format=format)),

        ])
        return Response(data)