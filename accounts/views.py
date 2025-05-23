from rest_framework import generics, permissions, status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import login
from django.db import IntegrityError
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView
from knox.auth import TokenAuthentication
from .models import User, OfferImage, Offer, OfferResponse
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer, OfferResponseSerializer, UserOfferAdminSerializer, UserOfferCreateSerializer
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


class PublicOfferCreateView(generics.CreateAPIView):
    serializer_class = UserOfferCreateSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        offer = serializer.save()
        images_data = self.request.FILES.getlist('images')
        for image_file in images_data:
            OfferImage.objects.create(offer_request=offer, image=image_file)
        return offer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"message": "Your offer request has been submitted. We will review it and contact you."},
            status=status.HTTP_201_CREATED
        )

class OfferAdminViewSet(viewsets.ModelViewSet):
    serializer_class = UserOfferAdminSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = Offer.objects.prefetch_related('images', 'admin_responses').all()
    http_method_names = ['get', 'put', 'patch', 'head', 'options', 'post']

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['full_name', 'email', 'phone', 'details']
    ordering_fields = ['created_at',  'offer_type']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()

        return queryset

    @action(detail=True, methods=['post'], serializer_class=OfferResponseSerializer, url_path='respond')
    def create_admin_response(self, request, pk=None):
        user_offer_instance = self.get_object()
        serializer = OfferResponseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user_offer=user_offer_instance, admin_user=request.user)
            serializer.save(user_offer=user_offer_instance)
            user_offer_instance.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['get'], serializer_class=OfferResponseSerializer, url_path='responses')
    def list_admin_responses(self, request, pk=None):
        user_offer = self.get_object()
        responses = user_offer.admin_responses.all()
        serializer = OfferResponseSerializer(responses, many=True)
        return Response(serializer.data)

class OfferResponseAdminViewSet(viewsets.ModelViewSet):
    serializer_class = OfferResponseSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = OfferResponse.objects.all()
    http_method_names = ['get', 'put', 'patch', 'post', 'head', 'options']
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