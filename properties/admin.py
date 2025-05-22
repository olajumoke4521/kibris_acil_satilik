from django import forms
from django.contrib import admin
from .models import (
    Location,
    PropertyAdvertisement,
    PropertyImage,
    PropertyExplanation,
    PropertyExternalFeature,
    PropertyInteriorFeature
)

class PropertyAdvertisementAdminForm(forms.ModelForm):
    city = forms.CharField(
        max_length=100,
        required=False,
        help_text="City for the property location. Clear this to remove location."
    )
    area = forms.CharField(
        max_length=100,
        required=False,
        help_text="Area/District within the city (optional)."
    )

    class Meta:
        model = PropertyAdvertisement

        exclude = ('location',)


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            if self.instance.location:
                self.initial['city'] = self.instance.location.city
                self.initial['area'] = self.instance.location.area
            else:

                self.initial['city'] = ''
                self.initial['area'] = ''


    def clean(self):
        cleaned_data = super().clean()
        city = cleaned_data.get('city')
        area = cleaned_data.get('area')

        if area and not city:
            self.add_error('city', 'City is required if an area is specified.')
            self.add_error('area', 'Cannot specify an area without a city.')

        return cleaned_data


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'city', 'area')
    search_fields = ('city', 'area')
    list_filter = ('city',)
    ordering = ('city', 'area')


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    readonly_fields = ('uploaded_at',)
    fields = ('image', 'is_cover', 'uploaded_at')

class PropertyExplanationInline(admin.StackedInline):
    model = PropertyExplanation
    can_delete = True
    verbose_name_plural = 'Explanation'

class PropertyExternalFeatureInline(admin.StackedInline):
    model = PropertyExternalFeature
    can_delete = True
    verbose_name_plural = 'External Features'

class PropertyInteriorFeatureInline(admin.StackedInline):
    model = PropertyInteriorFeature
    can_delete = True
    verbose_name_plural = 'Interior Features'

@admin.register(PropertyAdvertisement)
class PropertyAdvertisementAdmin(admin.ModelAdmin):
    form = PropertyAdvertisementAdminForm # Use the custom form

    list_display = (
        'id', 'title', 'user_email', 'location_display', 'price_with_currency',
        'property_type', 'advertisement_type', 'is_active', 'advertise_status', 'published_date'
    )
    list_filter = (
        'is_active', 'advertise_status', 'property_type', 'advertisement_type',
        'price_currency', 'location__city', 'published_date', 'created_at',
        'furnished', 'swap', 'available_for_loan'
    )
    search_fields = (
        'title', 'id', 'user__email', 'location__city', 'location__area', 'address'
    )
    ordering = ('-published_date',)
    readonly_fields = ('id', 'published_date', 'created_at', 'updated_at')
    autocomplete_fields = ['user']

    fieldsets = (
        ('Core Information', {'fields': ('user', 'title', 'city', 'area', 'address')}),
        ('Status & Type', {'fields': ('is_active', 'advertise_status', 'advertisement_type', 'property_type', 'room_type')}),
        ('Pricing', {'fields': ('price', 'price_currency')}),
        ('Area', {'fields': ('gross_area', 'net_area', 'building_age', 'floor_location')}),
        ('Additional Details', {'fields': ('housing_shape', 'warming_type', 'furnished', 'swap')}),
        ('Financials', {'fields': ('dues', 'dues_currency', 'rent', 'rent_currency', 'available_for_loan')}),
        ('Timestamps', {'fields': ('published_date', 'created_at', 'updated_at')}),
    )
    inlines = [
        PropertyImageInline,
        PropertyExplanationInline,
        PropertyExternalFeatureInline,
        PropertyInteriorFeatureInline,
    ]

    def save_model(self, request, obj, form, change):
        city_input = form.cleaned_data.get('city')
        area_input = form.cleaned_data.get('area')

        if city_input and city_input.strip():
            city = city_input.strip()
            area = area_input.strip() if area_input and area_input.strip() else None

            location_obj, created = Location.objects.get_or_create(
                city=city,
                area=area
            )
            obj.location = location_obj
        else:
            obj.location = None

        super().save_model(request, obj, form, change)


    def user_email(self, obj):
        return obj.user.email if obj.user else '-'
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'

    def location_display(self, obj):
        return str(obj.location) if obj.location else '-'
    location_display.short_description = 'Location'
    location_display.admin_order_field = 'location__city'

    def price_with_currency(self, obj):
        return f"{obj.price} {obj.price_currency}"
    price_with_currency.short_description = 'Price'
    price_with_currency.admin_order_field = 'price'


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_property_ad_title', 'image_preview', 'is_cover', 'uploaded_at')
    list_filter = ('is_cover', 'property_ad__location__city', 'uploaded_at')
    search_fields = ('property_ad__title', 'property_ad__id')
    readonly_fields = ('uploaded_at', 'image_preview_large')
    autocomplete_fields = ['property_ad']

    def get_property_ad_title(self, obj):
        return obj.property_ad.title if obj.property_ad else "N/A"
    get_property_ad_title.short_description = 'Property Ad'
    get_property_ad_title.admin_order_field = 'property_ad__title'

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


@admin.register(PropertyExplanation)
class PropertyExplanationAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_property_ad_title', 'explanation_snippet')
    search_fields = ('property_ad__title', 'property_ad__id', 'explanation')
    autocomplete_fields = ['property_ad']

    def get_property_ad_title(self, obj):
        return obj.property_ad.title if obj.property_ad else "N/A"
    get_property_ad_title.short_description = 'Property Ad'
    get_property_ad_title.admin_order_field = 'property_ad__title'

    def explanation_snippet(self, obj):
        return (obj.explanation[:75] + '...') if len(obj.explanation) > 75 else obj.explanation
    explanation_snippet.short_description = 'Explanation'

@admin.register(PropertyExternalFeature)
class PropertyExternalFeatureAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_property_ad_title', 'elevator', 'gardened', 'security', 'car_park', 'swimming_pool')
    list_filter = ('elevator', 'gardened', 'fitness', 'security', 'thermal_insulation', 'doorman', 'car_park', 'playground', 'swimming_pool')
    search_fields = ('property_ad__title', 'property_ad__id')
    autocomplete_fields = ['property_ad']

    def get_property_ad_title(self, obj):
        return obj.property_ad.title if obj.property_ad else "N/A"
    get_property_ad_title.short_description = 'Property Ad'
    get_property_ad_title.admin_order_field = 'property_ad__title'

@admin.register(PropertyInteriorFeature)
class PropertyInteriorFeatureAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_property_ad_title', 'balcony', 'air_conditioning', 'furnished', 'jacuzzi', 'fireplace')
    list_filter = ('adsl', 'alarm', 'balcony', 'built_in_kitchen', 'furnished', 'air_conditioning', 'jacuzzi', 'fireplace', 'parent_bathroom')
    search_fields = ('property_ad__title', 'property_ad__id')
    autocomplete_fields = ['property_ad']

    def get_property_ad_title(self, obj):
        return obj.property_ad.title if obj.property_ad else "N/A"
    get_property_ad_title.short_description = 'Property Ad'
    get_property_ad_title.admin_order_field = 'property_ad__title'