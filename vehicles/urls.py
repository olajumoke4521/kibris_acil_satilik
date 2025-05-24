from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'admin', views.CarAdminViewSet, basename='admin-car')

urlpatterns = [
# Public URLs
    path('', views.PublicCarListView.as_view(), name='public-car-list'),
    path('<int:pk>/', views.PublicCarDetailView.as_view(), name='public-car-detail'),
    path('features/external/', views.CarExternalFeaturesMetadataView.as_view(),
         name='car-external-features-metadata'),
    path('features/internal/', views.CarInternalFeaturesMetadataView.as_view(),
         name='car-internal-features-metadata'),
    path('admin/form-schema/', views.CarAdvertisementFormSchemaView.as_view(), name='car_ad_form_schema'),

    # Admin URLs
    path('', include(router.urls)),

]