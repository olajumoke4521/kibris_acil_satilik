from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from django import forms
from .models import User


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