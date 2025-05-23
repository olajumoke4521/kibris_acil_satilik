"""
URL configuration for kibris_acil_satilik project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import APIRootView, DashboardTotalsView
from properties.views import LatestAdvertisementsView, CombinedFilterOptionsView, PropertyBasicListView
from vehicles.views import CarBasicListView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', APIRootView.as_view(), name='api-root'),
    path('api/accounts/', include('accounts.urls')),
    path('api/properties/', include('properties.urls')),
    path('api/cars/', include('vehicles.urls')),
    path('api/latest-advertisements/', LatestAdvertisementsView.as_view(), name='public-latest-combined-ads'),
    path('api/filter-options/', CombinedFilterOptionsView.as_view(), name='public-all-filter-options'),
    path('api/totals/', DashboardTotalsView.as_view(), name='dashboard-totals'),
    path('api/propertiesbasic/', PropertyBasicListView.as_view(), name='property-basic-list'),
    path('api/carsbasic/', CarBasicListView.as_view(), name='car-basic-list'),


]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)