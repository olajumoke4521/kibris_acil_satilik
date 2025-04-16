from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.conf import settings

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_membership = models.DateTimeField(default=timezone.now, blank=True, null=True)
    photo = models.ImageField(upload_to='user_photos/', blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])])

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name='customers')
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    mobile_number = models.CharField(max_length=20)
    mobile_number_2 = models.CharField(max_length=20, blank=True, null=True)
    mobile_number_3 = models.CharField(max_length=20, blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    telephone_2 = models.CharField(max_length=20, blank=True, null=True)
    telephone_3 = models.CharField(max_length=20, blank=True, null=True)
    fax = models.CharField(max_length=20, blank=True, null=True)

    ADVERTISE_TYPE_CHOICES = [
        ('sale', 'Sale'),
        ('rent', 'Rent'),
    ]
    type_of_advertise = models.CharField(max_length=10, choices=ADVERTISE_TYPE_CHOICES, default='sale')

    CUSTOMER_ROLE_CHOICES = [
        ('active', 'Active'),
        ('passive', 'Passive'),
    ]
    customer_role = models.CharField(max_length=10, choices=CUSTOMER_ROLE_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.type_of_advertise}"


class CustomerOffer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
        ('6+', '6+'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('contacted', 'Contacted'),
        ('closed', 'Closed'),
    ]
    name = models.CharField(max_length=255)
    address = models.TextField()
    unit_number = models.CharField(max_length=50)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    room_type = models.CharField(max_length=100, choices=ROOM_TYPE_CHOICES)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Contact information
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    # Type of offer (property or vehicle)
    # OFFER_TYPE_CHOICES = [
    #    ('property', 'Property'),
    #    ('vehicle', 'Vehicle'),
    #]
    #offer_type = models.CharField(max_length=10, choices=OFFER_TYPE_CHOICES, default='property')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Offer from {self.name} - {self.created_at.strftime('%Y-%m-%d')}"


class OfferImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    offer = models.ForeignKey(CustomerOffer, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(
        upload_to='offer_images/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Offer {self.offer.id} ({self.offer.name})"