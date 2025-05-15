from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'admin', views.CarAdminViewSet, basename='admin-car')

urlpatterns = [
# Public URLs
    path('', views.PublicCarListView.as_view(), name='public-car-list'),
    path('<uuid:pk>/', views.PublicCarDetailView.as_view(), name='public-car-detail'),
    path('features/external/', views.CarExternalFeaturesMetadataView.as_view(),
         name='car-external-features-metadata'),
    path('features/internal/', views.CarInternalFeaturesMetadataView.as_view(),
         name='car-internal-features-metadata'),

    # Admin URLs
    path('admin/create-customer-and-car/', views.CreateCustomerAndCarView.as_view(), name='create_customer_and_car'),
    path('', include(router.urls)),

]