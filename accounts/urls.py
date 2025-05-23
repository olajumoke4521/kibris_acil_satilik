# accounts/urls.py

from django.urls import path, include
from knox import views as knox_views
from rest_framework.routers import DefaultRouter
from .views import RegisterView, LoginView, UserDetailView, PublicOfferCreateView, OfferAdminViewSet, \
    OfferResponseAdminViewSet

router = DefaultRouter()
router.register(r'admin/offers', OfferAdminViewSet, basename='admin-offer')
router.register(r'admin/offer-responses', OfferResponseAdminViewSet, basename='admin-offer-response')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', knox_views.LogoutView.as_view(), name='logout'),
    path('logoutall/', knox_views.LogoutAllView.as_view(), name='logoutall'),  # Logout from all devices
    path('user/', UserDetailView.as_view(), name='user-detail'),

    # Public endpoint for creating offers
    path('offers/submit/', PublicOfferCreateView.as_view(), name='public-offer-submit'),

    path('', include(router.urls)),

]