from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'admin', views.PropertyAdminViewSet, basename='admin-property')

urlpatterns = [
# Public URLs
    path('', views.PublicPropertyListView.as_view(), name='public-property-list'),
    path('<int:pk>/', views.PublicPropertyDetailView.as_view(), name='public-property-detail'),
    path('features/external/', views.PropertyExternalFeaturesMetadataView.as_view(),
         name='property-external-features-metadata'),
    path('features/interior/', views.PropertyInteriorFeaturesMetadataView.as_view(),
         name='property-interior-features-metadata'),
    path('admin/form-schema/', views.PropertyAdvertisementFormSchemaView.as_view(), name='property_ad_form_schema'),

    # Admin URLs
    path('', include(router.urls)),
]