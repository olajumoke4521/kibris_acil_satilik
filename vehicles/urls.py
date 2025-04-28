from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'admin/cars', views.CarAdminViewSet, basename='admin-car')

urlpatterns = [
    # Admin URLs
    path('', include(router.urls)),

    path('admin/create-customer-and-car/', views.CreateCustomerAndCarView.as_view(), name='create_customer_and_car'),
    # Public URLs
    path('cars/', views.PublicCarListView.as_view(), name='public-car-list'),
    path('cars/<uuid:pk>/', views.PublicCarDetailView.as_view(), name='public-car-detail'),
]