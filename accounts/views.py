from rest_framework import generics, permissions, status, viewsets, filters
from rest_framework.response import Response
from django.contrib.auth import login
from django.db import IntegrityError
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView
from knox.auth import TokenAuthentication
from .models import User, Customer, CustomerOffer, OfferImage
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer, CustomerSerializer, CustomerOfferSerializer, CustomerOfferCreateSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from collections import OrderedDict
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny


class RegisterView(generics.CreateAPIView):
    """View for user registration - only allows one user to be created"""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def create(self, request, *args, **kwargs):
        if User.objects.exists():
            return Response(
                {"detail": "Registration is closed. A user already exists."},
                status=status.HTTP_403_FORBIDDEN
            )

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
                "message": "Admin User registered successfully"
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


class CustomerViewSet(viewsets.ModelViewSet):
    """Viewset for Customer objects"""
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        """Return customers for the current user only"""
        return Customer.objects.filter(user=self.request.user).order_by('-created_at')


    def perform_create(self, serializer):
        """Save the customer with the current user"""
        serializer.save(user=self.request.user)


class CustomerOfferViewSet(viewsets.ModelViewSet):
    """ViewSet for managing customer offers (admin only)"""
    serializer_class = CustomerOfferSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    search_fields = ['name', 'email', 'phone', 'address', 'description']
    ordering_fields = ['created_at', 'status', 'name']

    def get_queryset(self):
        """Return all customer offers ordered by creation date"""
        queryset = CustomerOffer.objects.prefetch_related('images').all().order_by('-created_at')

        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        start_date = self.request.query_params.get('start_date', None)
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)

        end_date = self.request.query_params.get('end_date', None)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        return queryset


class PublicCustomerOfferCreateView(generics.CreateAPIView):
    """View for creating customer offers (public, no authentication required)"""
    serializer_class = CustomerOfferCreateSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        """
        Save the offer instance and then handle uploaded images.
        """
        offer = serializer.save()

        images_data = self.request.FILES.getlist('images')
        for image_file in images_data:
            OfferImage.objects.create(offer=offer, image=image_file)

    def create(self, request, *args, **kwargs):
        """
        Override create to provide a custom success message and handle images.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_data = {
            "message": "Your offer request has been submitted successfully. We will review it and contact you soon.",
        }
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


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
            ('customers', reverse('customer-list', request=request, format=format)),
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