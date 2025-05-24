from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from django import forms
from .models import User, Offer, CarOffer, PropertyOffer, OfferImage, OfferResponse


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'phone', 'photo')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('email', 'password', 'phone', 'photo', 'date_of_membership',
                  'is_active', 'is_staff', 'is_admin')


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('email', 'phone', 'date_of_membership', 'is_staff', 'is_admin', 'is_active')
    list_filter = ('is_staff', 'is_admin', 'is_active', 'date_of_membership')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('phone', 'photo')}),
        ('Permissions', {'fields': ('is_admin', 'is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_of_membership')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'photo', 'password1', 'password2'),
        }),
    )

    search_fields = ('email', 'phone')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions')
    readonly_fields = ('date_of_membership', 'last_login')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('id',)
        return self.readonly_fields


admin.site.register(User, UserAdmin)


class CarOfferInline(admin.StackedInline):
    model = CarOffer
    can_delete = True
    verbose_name_plural = 'Car Specific Details'
    fk_name = 'offer'

    extra = 0

class PropertyOfferInline(admin.StackedInline):
    model = PropertyOffer
    can_delete = True
    verbose_name_plural = 'Property Specific Details'
    fk_name = 'offer'
    # fields = ['address', 'build_date', 'square_meter', 'room_type', 'document_type']
    extra = 0

class OfferImageInline(admin.TabularInline):
    model = OfferImage
    fields = ('image_preview', 'image', 'is_cover_image', 'is_active', 'uploaded_at')
    readonly_fields = ('image_preview', 'uploaded_at',)
    extra = 1
    ordering = ('-is_cover_image', '-uploaded_at')

    def image_preview(self, obj):
        from django.utils.html import mark_safe
        if obj.image:
            return mark_safe(f'<a href="{obj.image.url}" target="_blank"><img src="{obj.image.url}" style="max-height: 100px; max-width: 100px;" /></a>')
        return "(No image)"
    image_preview.short_description = 'Preview'

class OfferResponseInline(admin.StackedInline):
    model = OfferResponse
    fields = ('price', 'currency', 'description', 'offer_date', 'created_by', 'offered_by', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    extra = 0
    autocomplete_fields = ['created_by', 'offered_by']
    ordering = ('-offer_date',)

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'offer_type', 'city', 'area', 'price_display', 'is_active', 'created_at')
    list_filter = ('offer_type', 'is_active', 'city', 'created_at')
    search_fields = ('full_name', 'email', 'phone', 'details', 'city', 'area', 'id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('full_name', 'email', 'phone', 'details')
        }),
        ('Offer Core Details', {
            'fields': ('offer_type', 'city', 'area', 'price', 'currency', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [CarOfferInline, PropertyOfferInline, OfferImageInline, OfferResponseInline]

    def price_display(self, obj):
        return f"{obj.price} {obj.currency}"
    price_display.short_description = 'Price'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        offer = form.instance
        if offer.offer_type == 'car':
            PropertyOffer.objects.filter(offer=offer).delete()
        elif offer.offer_type == 'property':
            CarOffer.objects.filter(offer=offer).delete()


@admin.register(CarOffer)
class CarOfferAdmin(admin.ModelAdmin):
    list_display = ('offer_id_link', 'model', 'brand', 'kilometer', 'model_year', 'is_active')
    list_filter = ('brand', 'fuel_type', 'transmission', 'is_active', 'model_year')
    search_fields = ('offer__full_name', 'model', 'brand', 'offer__id')
    autocomplete_fields = ['offer']
    readonly_fields = ('offer',)

    def offer_id_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse("admin:your_app_name_offer_change", args=[obj.offer.id])
        return format_html('<a href="{}">{} (View Offer)</a>', link, obj.offer.id)
    offer_id_link.short_description = 'Offer ID'
    offer_id_link.admin_order_field = 'offer__id'


@admin.register(PropertyOffer)
class PropertyOfferAdmin(admin.ModelAdmin):
    list_display = ('offer_id_link', 'address_short', 'room_type', 'document_type', 'is_active')
    list_filter = ('document_type', 'room_type', 'is_active', 'offer__city')
    search_fields = ('offer__full_name', 'address', 'offer__id')
    autocomplete_fields = ['offer']
    readonly_fields = ('offer',)

    def offer_id_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse("admin:your_app_name_offer_change", args=[obj.offer.id]) # Replace your_app_name
        return format_html('<a href="{}">{} (View Offer)</a>', link, obj.offer.id)
    offer_id_link.short_description = 'Offer ID'
    offer_id_link.admin_order_field = 'offer__id'

    def address_short(self, obj):
        return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address
    address_short.short_description = 'Address'


@admin.register(OfferImage)
class OfferImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image_preview_list', 'is_cover_image', 'is_active', 'uploaded_at')
    list_filter = ('is_cover_image', 'is_active', 'offer__offer_type')
    search_fields = ('offer__full_name', 'offer__id', 'image')
    autocomplete_fields = ['offer']
    readonly_fields = ('image_preview_change', 'uploaded_at',)
    fields = ('offer', 'image', 'image_preview_change', 'is_cover_image', 'is_active', 'uploaded_at')
    ordering = ('-uploaded_at',)

    def image_preview_list(self, obj):
        from django.utils.html import mark_safe
        if obj.image:
            return mark_safe(f'<a href="{obj.image.url}" target="_blank"><img src="{obj.image.url}" style="max-height: 50px; max-width: 50px;" /></a>')
        return "(No image)"
    image_preview_list.short_description = 'Image'

    def image_preview_change(self, obj): # For change form
        from django.utils.html import mark_safe
        if obj.image:
            return mark_safe(f'<a href="{obj.image.url}" target="_blank"><img src="{obj.image.url}" style="max-height: 200px; max-width: 200px;" /></a><br/>Current: {obj.image.name}')
        return "No image uploaded yet."
    image_preview_change.short_description = 'Image Preview'


    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(OfferResponse)
class OfferResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'price_display', 'created_by_email', 'offered_by_email', 'offer_date', 'is_active')
    list_filter = ('is_active', 'offer_date', 'currency', 'created_by', 'offered_by')
    search_fields = ('offer__full_name', 'description', 'created_by__email', 'offered_by__email', 'offer__id')
    autocomplete_fields = ['offer', 'created_by', 'offered_by']
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('offer', ('price', 'currency'), 'description', 'offer_date')}),
        ('Attribution', {'fields': ('created_by', 'offered_by')}),
        ('Status & Timestamps', {'fields': ('is_active', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    ordering = ('-offer_date',)


    def price_display(self, obj):
        return f"{obj.price} {obj.currency}"
    price_display.short_description = 'Offer Price'

    def created_by_email(self, obj):
        return obj.created_by.email if obj.created_by else None
    created_by_email.short_description = 'Created By'
    created_by_email.admin_order_field = 'created_by__email'

    def offered_by_email(self, obj):
        return obj.offered_by.email if obj.offered_by else None
    offered_by_email.short_description = 'Offered By'
    offered_by_email.admin_order_field = 'offered_by__email'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            if not obj.created_by:
                obj.created_by = request.user
        super().save_model(request, obj, form, change)