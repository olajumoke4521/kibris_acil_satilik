from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'admin/properties', views.PropertyAdminViewSet, basename='admin-property')

urlpatterns = [
    # Admin URLs
    path('', include(router.urls)),

    path('admin/create-customer-and-property/', views.CreateCustomerAndPropertyView.as_view(), name='create_customer_and_ad'),

    # Public URLs
    path('properties/', views.PublicPropertyListView.as_view(), name='public-property-list'),
    path('properties/<uuid:pk>/', views.PublicPropertyDetailView.as_view(), name='public-property-detail'),
]