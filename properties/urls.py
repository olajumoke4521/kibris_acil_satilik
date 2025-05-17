from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'admin', views.PropertyAdminViewSet, basename='admin-property')

urlpatterns = [
# Public URLs
    path('', views.PublicPropertyListView.as_view(), name='public-property-list'),
    path('<uuid:pk>/', views.PublicPropertyDetailView.as_view(), name='public-property-detail'),
    path('features/external/', views.PropertyExternalFeaturesMetadataView.as_view(),
         name='property-external-features-metadata'),
    path('features/interior/', views.PropertyInteriorFeaturesMetadataView.as_view(),
         name='property-interior-features-metadata'),

    # Admin URLs
    path('admin/create-customer-and-property/', views.CreateCustomerAndPropertyView.as_view(), name='create_customer_and_ad'),
    path('', include(router.urls)),
]