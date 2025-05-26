from django.contrib import admin
from .models import (
    CarAdvertisement,
    CarImage,
    CarExplanation,
    CarInternalFeature,
    CarExternalFeature
)

class CarImageInline(admin.TabularInline):
    model = CarImage
    extra = 1
    readonly_fields = ('uploaded_at',)
    fields = ('image', 'is_cover', 'uploaded_at')

class CarExplanationInline(admin.StackedInline):
    model = CarExplanation
    can_delete = True
    verbose_name_plural = 'Explanation'

class CarInternalFeatureInline(admin.StackedInline):
    model = CarInternalFeature
    can_delete = True
    verbose_name_plural = 'Internal Features'

class CarExternalFeatureInline(admin.StackedInline):
    model = CarExternalFeature
    can_delete = True
    verbose_name_plural = 'External Features'

@admin.register(CarAdvertisement)
class CarAdvertisementAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'user_email', 'price_with_currency', 'brand_series_model',
        'is_active', 'advertise_status', 'published_date'
    )
    list_filter = (
        'is_active', 'advertise_status', 'vehicle_type', 'advertisement_type', 'price_type',
        'brand', 'model_year', 'transmission', 'fuel_type', 'steering_type', 'published_date'
    )
    search_fields = (
        'title', 'id', 'user__email', 'brand', 'series', 'address', 'explanation__explanation'
    )
    ordering = ('-published_date',)
    readonly_fields = ('id', 'published_date', 'created_at', 'updated_at')
    autocomplete_fields = ['user']

    fieldsets = (
        ('Core Information', {'fields': ('user', 'title', 'address')}),
        ('Status & Type', {'fields': ('is_active', 'advertise_status', 'advertisement_type', 'vehicle_type')}),
        ('Pricing', {'fields': ('price', 'price_type')}),
        ('Vehicle Specs', {'fields': (
            'brand', 'series', 'model_year', 'color', 'transmission',
            'fuel_type', 'steering_type', 'engine_displacement', 'engine_power'
        )}),
        ('Timestamps', {'fields': ('published_date', 'created_at', 'updated_at')}),
    )
    inlines = [
        CarImageInline,
        CarExplanationInline,
        CarInternalFeatureInline,
        CarExternalFeatureInline,
    ]

    def user_email(self, obj):
        return obj.user.email if obj.user else '-'
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'

    def price_with_currency(self, obj):
        return f"{obj.price} {obj.price_type}"
    price_with_currency.short_description = 'Price'
    price_with_currency.admin_order_field = 'price'

    def brand_series_model(self, obj):
        return f"{obj.brand or ''} {obj.series or ''} ({obj.model_year or ''})"
    brand_series_model.short_description = 'Vehicle'


@admin.register(CarImage)
class CarImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_car_ad_title', 'image_preview', 'is_cover', 'uploaded_at')
    list_filter = ('is_cover', 'uploaded_at')
    search_fields = ('car_ad__title', 'car_ad__id')
    readonly_fields = ('uploaded_at', 'image_preview_large')
    autocomplete_fields = ['car_ad']

    def get_car_ad_title(self, obj):
        return obj.car_ad.title if obj.car_ad else "N/A"
    get_car_ad_title.short_description = 'Car Ad'
    get_car_ad_title.admin_order_field = 'car_ad__title'

    def image_preview(self, obj):
        from django.utils.html import format_html
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image'

    def image_preview_large(self, obj):
        from django.utils.html import format_html
        if obj.image:
            return format_html('<img src="{}" style="max-height: 200px; max-width: 200px;" />', obj.image.url)
        return "No Image"
    image_preview_large.short_description = 'Image Preview'

@admin.register(CarExplanation)
class CarExplanationAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_car_ad_title', 'explanation_snippet')
    search_fields = ('car_ad__title', 'car_ad__id', 'explanation')
    autocomplete_fields = ['car_ad']

    def get_car_ad_title(self, obj):
        return obj.car_ad.title if obj.car_ad else "N/A"
    get_car_ad_title.short_description = 'Car Ad'
    get_car_ad_title.admin_order_field = 'car_ad__title'

    def explanation_snippet(self, obj):
        return (obj.explanation[:75] + '...') if len(obj.explanation) > 75 else obj.explanation
    explanation_snippet.short_description = 'Explanation'

@admin.register(CarInternalFeature)
class CarInternalFeatureAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_car_ad_title', 'leather_steering_wheel', 'cruise_control', 'reverse_view_camera', 'air_conditioner_digital')
    list_filter = ('fabric_armchair', 'leather_fabric_armchair', 'keyless_drive', 'cruise_control', 'reverse_view_camera', 'air_conditioner_digital')
    search_fields = ('car_ad__title', 'car_ad__id')
    autocomplete_fields = ['car_ad']

    def get_car_ad_title(self, obj):
        return obj.car_ad.title if obj.car_ad else "N/A"
    get_car_ad_title.short_description = 'Car Ad'
    get_car_ad_title.admin_order_field = 'car_ad__title'

@admin.register(CarExternalFeature)
class CarExternalFeatureAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_car_ad_title', 'headlamp_xenon', 'parking_sensor_rear', 'alloy_wheel', 'rain_sensor')
    list_filter = ('headlamp_xenon', 'headlight_adaptive', 'electric_mirrors', 'parking_sensor_rear', 'rain_sensor', 'alloy_wheel')
    search_fields = ('car_ad__title', 'car_ad__id')
    autocomplete_fields = ['car_ad']

    def get_car_ad_title(self, obj):
        return obj.car_ad.title if obj.car_ad else "N/A"
    get_car_ad_title.short_description = 'Car Ad'
    get_car_ad_title.admin_order_field = 'car_ad__title'