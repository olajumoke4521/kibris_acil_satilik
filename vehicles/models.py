from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from accounts.models import User
from properties.constants import PREDEFINED_CAR_DATA
from django.utils.translation import gettext_lazy as _

# --- Helper function to generate choices ---
def generate_brand_choices(car_data):
    choices = []
    for display_name in PREDEFINED_CAR_DATA.keys():
        internal_value = display_name.lower().replace('-', '').replace(' ', '')
        choices.append((internal_value, display_name))
    return sorted(choices, key=lambda x: x[1])

def generate_series_choices(car_data):
    all_series = set()
    for brand_details in car_data.values():
        for series_name in brand_details.get("series", []):
            all_series.add(series_name)
    return sorted([(series.lower().replace(" ", "-"), series) for series in all_series])

BRAND_CHOICES = generate_brand_choices(PREDEFINED_CAR_DATA)
SERIES_CHOICES = generate_series_choices(PREDEFINED_CAR_DATA)

class CarAdvertisement(models.Model):
    id = models.AutoField(primary_key=True)
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
    price_type = models.CharField(max_length=3, choices=PRICE_TYPE_CHOICES, default='GBP')
    VEHICLE_TYPE_CHOICES = [
        ('sedan', 'Sedan'), ('suv', 'SUV'), ('hatchback', 'Hatchback'),
        ('pickup', 'Pickup'), ('cabrio', 'Cabrio'), ('minivan', 'Minivan'),
    ]
    VEHICLE_TYPE_CHOICES_TR = [
        ('sedan', 'Sedan'), ('suv', 'SUV'), ('hatchback', 'Heçbek'),
        ('pickup', 'Pikap'), ('cabrio', 'Kabriyo'), ('minivan', 'Minivan'),
    ]
    vehicle_type = models.CharField(max_length=50, choices=VEHICLE_TYPE_CHOICES)
    ADVERTISEMENT_TYPE_CHOICES = [
        ('sale', 'For Sale'),
        ('rent', 'For Rent'),
    ]
    ADVERTISEMENT_TYPE_CHOICES_TR = [
        ('sale', 'Satılık'),
        ('rent', 'Kiralık'),
    ]
    advertisement_type = models.CharField(max_length=50, choices=ADVERTISEMENT_TYPE_CHOICES)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    area = models.CharField(max_length=100, blank=True, null=True)

    ADVERT_STATUS_CHOICES = [
        ('on', 'On'), ('off', 'Off'),
    ]
    ADVERT_STATUS_CHOICES_TR = [
        ('on', 'Yayında'),
        ('off', 'Yayında Değil'),
    ]
    advertise_status = models.CharField(max_length=10, choices=ADVERT_STATUS_CHOICES, default='on')
    published_date = models.DateTimeField(auto_now_add=True)

    TRANSMISSION_CHOICES = [
        ('automatic', 'Automatic'), ('manual', 'Manual'), ('semi-automatic', 'Semi-Automatic'),
    ]
    TRANSMISSION_CHOICES_TR = [
        ('automatic', 'Otomatik'), ('manual', 'Manuel'), ('semi-automatic', 'Yarı Otomatik'),
    ]
    transmission = models.CharField(max_length=15, choices=TRANSMISSION_CHOICES)
    color = models.CharField(max_length=50, blank=True, null=True)

    brand = models.CharField(max_length=100, choices=BRAND_CHOICES, blank=True, null=True)
    series = models.CharField(max_length=100, choices=SERIES_CHOICES, blank=True, null=True)
    model_year = models.IntegerField()
    FUEL_TYPE_CHOICES = [
        ('diesel', 'Diesel'), ('gasoline', 'Gasoline'), ('lpg', 'LPG'),
        ('hybrid', 'Hybrid'), ('electric', 'Electric'),
    ]
    FUEL_TYPE_CHOICES_TR = [
        ('diesel', 'Dizel'), ('gasoline', 'Benzin'), ('lpg', 'LPG'),
        ('hybrid', 'Hibrit'), ('electric', 'Elektrikli'),
    ]
    fuel_type = models.CharField(max_length=50, choices=FUEL_TYPE_CHOICES, blank=True, null=True)

    STEERING_TYPE_CHOICES = [
        ('right_steering_wheel', 'Right-Hand Drive'),
        ('left_steering_wheel', 'Left-Hand Drive'),
    ]
    STEERING_TYPE_CHOICES_TR = [
        ('right_steering_wheel', 'Sağ Direksiyon'),
        ('left_steering_wheel', 'Sol Direksiyon'),
    ]
    steering_type = models.CharField(max_length=50, choices=STEERING_TYPE_CHOICES)
    engine_displacement = models.IntegerField(blank=True, null=True)
    engine_power = models.IntegerField(blank=True, null=True)
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

    fabric_armchair = models.BooleanField(default=False, verbose_name=_("Fabric Armchair"))
    leather_fabric_armchair = models.BooleanField(default=False, verbose_name=_("Leather-Fabric Armchair"))
    electric_windshields = models.BooleanField(default=False, verbose_name=_("Electric Windshields"))
    front_armrest = models.BooleanField(default=False, verbose_name=_("Front Armrest"))
    rear_armrest = models.BooleanField(default=False, verbose_name=_("Rear Armrest"))
    keyless_drive = models.BooleanField(default=False, verbose_name=_("Keyless Drive"))
    forward_gear = models.BooleanField(default=False, verbose_name=_("Forward Gear"))
    hydraulic_steering = models.BooleanField(default=False, verbose_name=_("Hydraulic Steering"))
    functional_steering_wheel = models.BooleanField(default=False, verbose_name=_("Functional Steering Wheel"))
    adjustable_steering_wheel = models.BooleanField(default=False, verbose_name=_("Adjustable Steering Wheel"))
    leather_steering_wheel = models.BooleanField(default=False, verbose_name=_("Leather Steering Wheel"))
    cruise_control = models.BooleanField(default=False, verbose_name=_("Cruise Control"))
    adaptive_cruise_control = models.BooleanField(default=False, verbose_name=_("Adaptive Cruise Control"))
    reverse_view_camera = models.BooleanField(default=False, verbose_name=_("Reverse View Camera"))
    road_computer = models.BooleanField(default=False, verbose_name=_("Road Computer"))
    start_stop = models.BooleanField(default=False, verbose_name=_("Start-Stop System"))
    air_conditioner_digital = models.BooleanField(default=False, verbose_name=_("Digital Air Conditioner"))
    digital_monitor = models.BooleanField(default=False, verbose_name=_("Digital Monitor"))

    def __str__(self):
        return f"Internal Features for {self.car_ad.title}"


class CarExternalFeature(models.Model):
    id = models.AutoField(primary_key=True)
    car_ad = models.OneToOneField(CarAdvertisement, on_delete=models.CASCADE, related_name='external_features')

    headlamp_xenon = models.BooleanField(default=False, verbose_name=_("Xenon Headlamps"))
    headlight_adaptive = models.BooleanField(default=False, verbose_name=_("Adaptive Headlights"))
    headlight_sensor = models.BooleanField(default=False, verbose_name=_("Headlight Sensor"))
    electric_mirrors = models.BooleanField(default=False, verbose_name=_("Electric Mirrors"))
    folding_mirrors = models.BooleanField(default=False, verbose_name=_("Folding Mirrors"))
    mirrors_heated = models.BooleanField(default=False, verbose_name=_("Heated Mirrors"))
    parking_sensor_rear = models.BooleanField(default=False, verbose_name=_("Rear Parking Sensor"))
    parking_sensor_front = models.BooleanField(default=False, verbose_name=_("Front Parking Sensor"))
    rain_sensor = models.BooleanField(default=False, verbose_name=_("Rain Sensor"))
    alloy_wheel = models.BooleanField(default=False, verbose_name=_("Alloy Wheels"))
    rear_window_defroster = models.BooleanField(default=False, verbose_name=_("Rear Window Defroster"))
    smart_tailgate = models.BooleanField(default=False, verbose_name=_("Smart Tailgate"))

    def __str__(self):
        return f"External Features for {self.car_ad.title}"