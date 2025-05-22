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
    is_active = models.BooleanField(default=True)
    photo = models.ImageField(upload_to='user_photos/', blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])])

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


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
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Contact information
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
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