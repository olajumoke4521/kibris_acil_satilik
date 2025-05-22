import uuid
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from accounts.models import User


class CarAdvertisement(models.Model):
    id = models.AutoField(primary_key=True)
    advertise_no = models.CharField(max_length=20, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='car_advertisements')
    title = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    PRICE_TYPE_CHOICES = [
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('GBP', 'GBP'),
        ('TRY', 'TRY'),
    ]
    price_type = models.CharField(max_length=3, choices=PRICE_TYPE_CHOICES, default='TRY')
    VEHICLE_TYPE_CHOICES = [
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('hatchback', 'Hatchback'),
        ('pickup', 'Pickup'),
        ('cabrio', 'Cabrio'),
        ('minivan', 'Minivan'),
    ]
    VEHICLE_TYPE_CHOICES_TR = [
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('hatchback', 'Hatchback'),
        ('pickup', 'Toplama'),
        ('cabrio', 'Cabrio'),
        ('minivan', 'Minibüs'),
    ]
    vehicle_type = models.CharField(max_length=50, choices=VEHICLE_TYPE_CHOICES)
    ADVERTISEMENT_TYPE_CHOICES = [
        ('sale', 'Sale'),
        ('rent', 'Rent'),
    ]
    advertisement_type = models.CharField(max_length=50, choices=ADVERTISEMENT_TYPE_CHOICES)
    province = models.CharField(max_length=100, blank=True, null=True)
    neighborhood = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField()

    ADVERT_STATUS_CHOICES = [
        ('on', 'ON'),
        ('off', 'OFF'),
    ]
    advertise_status = models.CharField(max_length=10, choices=ADVERT_STATUS_CHOICES, default='on')
    published_date = models.DateTimeField(auto_now_add=True)

    GEAR_TYPE_CHOICES = [
        ('automatic', 'Automatic'),
        ('manual', 'Manual'),
        ('semi-automatic', 'Semi-Automatic'),
    ]
    gear_type = models.CharField(max_length=15, choices=GEAR_TYPE_CHOICES)
    color = models.CharField(max_length=50)

    brand = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    series = models.CharField(max_length=100, blank=True, null=True)
    model_year = models.IntegerField()
    case_type = models.CharField(max_length=50, blank=True, null=True)
    fuel_type = models.CharField(max_length=50, blank=True, null=True)

    STEERING_TYPE_CHOICES = [
        ('right_steering_wheel', 'Right Steering Wheel'),
        ('left_steering_wheel', 'Left Steering Wheel'),
    ]
    steering_type = models.CharField(max_length=20, choices=STEERING_TYPE_CHOICES)
    engine_displacement = models.CharField(max_length=50, blank=True, null=True)
    engine_power = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class CarImage(models.Model):
    id = models.AutoField(primary_key=True)
    car_ad = models.ForeignKey(CarAdvertisement, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(
        upload_to='car_images/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])],
    )
    is_cover = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_cover', 'uploaded_at']

    def save(self, *args, **kwargs):
        if self.is_cover:
            CarImage.objects.filter(car_ad=self.car_ad, is_cover=True).exclude(pk=self.pk).update(is_cover=False)
        super().save(*args, **kwargs)

    def __str__(self):
        status = " (Cover)" if self.is_cover else ""
        ad_title = self.car_ad.title if self.car_ad else "Unlinked"
        return f"Image for {ad_title}{status}"


class CarExplanation(models.Model):
    id = models.AutoField(primary_key=True)
    car_ad = models.OneToOneField(CarAdvertisement, on_delete=models.CASCADE, related_name='explanation')
    explanation = models.TextField()

    def __str__(self):
        return f"Explanation for {self.car_ad.title}"


class CarInternalFeature(models.Model):
    id = models.AutoField(primary_key=True)
    car_ad = models.OneToOneField(CarAdvertisement, on_delete=models.CASCADE, related_name='internal_features')

    fabric_armchair = models.BooleanField(default=False)
    leather_fabric_armchair = models.BooleanField(default=False)
    electric_windshields = models.BooleanField(default=False)
    front_armrest = models.BooleanField(default=False)
    rear_armrest = models.BooleanField(default=False)
    keyless_drive = models.BooleanField(default=False)
    forward_gear = models.BooleanField(default=False)
    hydraulic_steering = models.BooleanField(default=False)
    functional_steering_wheel = models.BooleanField(default=False)
    adjustable_steering_wheel = models.BooleanField(default=False)
    leather_steering_wheel = models.BooleanField(default=False)
    cruise_control = models.BooleanField(default=False)
    adaptive_cruise_control = models.BooleanField(default=False)
    reverse_view_camera = models.BooleanField(default=False)
    road_computer = models.BooleanField(default=False)
    start_stop = models.BooleanField(default=False)
    air_conditioner_digital = models.BooleanField(default=False)
    digital_monitor = models.BooleanField(default=False)

    def __str__(self):
        return f"Internal Features for {self.car_ad.title}"


class CarExternalFeature(models.Model):
    id = models.AutoField(primary_key=True)
    car_ad = models.OneToOneField(CarAdvertisement, on_delete=models.CASCADE, related_name='external_features')

    headlamp_xenon = models.BooleanField(default=False)
    headlight_adaptive = models.BooleanField(default=False)
    headlight_sensor = models.BooleanField(default=False)
    electric_mirrors = models.BooleanField(default=False)
    folding_mirrors = models.BooleanField(default=False)
    mirrors_heated = models.BooleanField(default=False)
    parking_sensor_rear = models.BooleanField(default=False)
    parking_sensor_front = models.BooleanField(default=False)
    rain_sensor = models.BooleanField(default=False)
    alloy_wheel = models.BooleanField(default=False)
    rear_window_defroster = models.BooleanField(default=False)
    smart_tailgate = models.BooleanField(default=False)

    def __str__(self):
        return f"External Features for {self.car_ad.title}"