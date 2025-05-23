from django.conf import settings
from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser,PermissionsMixin,Permission


class UserManager(BaseUserManager):

    def create_user(
            self,
            email,
            password=None, **extra_fields):

        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        if not password:
            raise ValueError("Users must have a password")

        user = self.model(
            email=email,
            password=password

        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        user = self.create_user(
            password=password,
            email=email
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_membership = models.DateTimeField(default=timezone.now, blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    photo = models.ImageField(upload_to='user_photos/', blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])])

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


class Offer(models.Model):
    id = models.AutoField(primary_key=True)
    OFFER_TYPE_CHOICES = [
        ('car', 'Car'),
        ('property', 'Property'),
    ]
    ROOM_TYPE_CHOICES = [
        ('1+0', '1+0'),
        ('1+1', '1+1'),
        ('2+1', '2+1'),
        ('2+2', '2+2'),
        ('3+1', '3+1'),
        ('3+2', '3+2'),
        ('4+1', '4+1'),
        ('4+2', '4+2'),
        ('5+1', '5+1'),
        ('5+2', '5+2'),
        ('5+3', '5+3'),
        ('5+4', '5+4'),
        ('6+1', '6+1'),
        ('6+2', '6+2'),
        ('6+3', '6+3'),
        ('6+4', '6+4'),
        ('7+1', '7+1'),
        ('7+2', '7+2'),
        ('7+3', '7+3'),
        ('8+', '8+'),
    ]
    full_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    offer_type = models.CharField(max_length=10, choices=OFFER_TYPE_CHOICES)
    details = models.TextField(blank=True, null=True)

    # Car Specific Fields
    model_name = models.CharField(max_length=100, blank=True, null=True)
    kilometers = models.PositiveIntegerField(blank=True, null=True, verbose_name="Kilometers (KM)")
    model_year = models.PositiveIntegerField(blank=True, null=True)

    # Property Specific Fields
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    area = models.CharField(max_length=100, blank=True, null=True)
    build_date = models.DateField(blank=True, null=True)
    square_meters = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                                 verbose_name="Area (m²)")
    room_type = models.CharField(max_length=50, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "User Offer Request"

    def __str__(self):
        return f"Offer ({self.get_offer_type_display()}) from {self.full_name} - {self.id}"


class OfferImage(models.Model):
    id = models.AutoField(primary_key=True)
    offer_request  = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(
        upload_to='offer_images/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Offer {self.offer_request .id}"


class OfferResponse(models.Model):
    id = models.AutoField(primary_key=True)
    user_offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='admin_responses')

    admin_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_offer_responses")

    offer_price = models.DecimalField(max_digits=20, decimal_places=2)
    CURRENCY_TYPE_CHOICES = [
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('GBP', 'GBP'),
        ('TRY', 'TRY'),
    ]
    offer_price_currency = models.CharField(max_length=3, choices=CURRENCY_TYPE_CHOICES, default='GBP')
    offer_description = models.TextField()
    offer_date = models.DateField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-offer_date']

    def __str__(self):
        return f"Admin Response to {self.user_offer.full_name}'s Offer ({self.user_offer.id}) - {self.offer_date.strftime('%Y-%m-%d')}"