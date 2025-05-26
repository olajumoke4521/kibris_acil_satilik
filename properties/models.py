from django.db import models
from django.core.validators import FileExtensionValidator
from accounts.models import User
from django.conf import settings

class Location(models.Model):
    id = models.AutoField(primary_key=True)
    city = models.CharField(max_length=100)
    area = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ('city', 'area')
        ordering = ['city', 'area']
        verbose_name = "Location"
        verbose_name_plural = "Locations"

    def __str__(self):
        parts = [self.city, self.area]
        return ' / '.join(part for part in parts if part)

class PropertyAdvertisement(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='property_advertisements')
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='properties', null=True, blank=True)

    title = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=20, decimal_places=2)
    is_active = models.BooleanField(default=True)

    CURRENCY_TYPE_CHOICES = [
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('GBP', 'GBP'),
        ('TRY', 'TRY'),
    ]
    price_currency = models.CharField(max_length=3, choices=CURRENCY_TYPE_CHOICES, default='GBP')
    address = models.TextField()

    ADVERT_STATUS_CHOICES = [
        ('on', 'ON'),
        ('off', 'OFF'),
    ]
    ADVERT_STATUS_CHOICES_TR = [
        ('on', 'Yayında'),
        ('off', 'Yayında Değil'),
    ]
    advertise_status = models.CharField(max_length=10, choices=ADVERT_STATUS_CHOICES, default='on')
    published_date = models.DateTimeField(auto_now_add=True)

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
    room_type = models.CharField(max_length=100, choices=ROOM_TYPE_CHOICES)

    PROPERTY_TYPE_CHOICES = [
        ('villa', 'Villa'),
        ('apartment', 'Apartment'),
        ('residence', 'Residence'),
        ('twin_villa', 'Twin Villa'),
        ('penthouse', 'Penthouse'),
        ('bungalow', 'Bungalow'),
        ('family_house', 'Family House'),
        ('complete_building', 'Complete Building'),
        ('timeshare', 'Timeshare'),
        ('abandoned_building', 'Abandoned Building'),
        ('half_construction', 'Half Construction'),
    ]
    PROPERTY_TYPE_CHOICES_TR = {
        'villa': 'Villa', 'apartment': 'Apartman',
        'residence': 'Rezidans',
        'twin_villa': 'İkiz Villa',
        'penthouse': 'Çatı katı',
        'bungalow': 'Bungalov',
        'family_house': 'Aile Evleri',
        'complete_building': 'Eksiksiz Bina',
        'timeshare': 'Devremülk',
        'abandoned_building': 'Terkedilmiş Bina',
        'half_construction': 'Yarım İnşaat'
    }
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPE_CHOICES)
    ADVERTISEMENT_TYPE_CHOICES = [
        ('sale', 'For Sale'),
        ('rent', 'For Rent'),
    ]
    ADVERTISEMENT_TYPE_CHOICES_TR = [
        ('sale', 'Satılık'),
        ('rent', 'Kiralık'),
    ]
    advertisement_type = models.CharField(max_length=50, choices=ADVERTISEMENT_TYPE_CHOICES)
    gross_area = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    net_area = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    building_age = models.IntegerField(blank=True, null=True)
    FLOOR_TYPE_CHOICES = [
        ('basement', 'Basement'),
        ('ground_floor', 'Ground Floor'),
        ('1', '1st Floor'),
        ('2', '2nd Floor'),
        ('3', '3rd Floor'),
        ('4+', '4th Floor or Higher'),
    ]
    floor_location = models.CharField(max_length=50, choices=FLOOR_TYPE_CHOICES, blank=True, null=True)
    housing_shape = models.CharField(max_length=20, blank=True, null=True)

    WARMING_TYPE_CHOICES = [
        ('natural_gas', 'Natural Gas'),
        ('central_heating', 'Central Heating'),
        ('underfloor_heating', 'Underfloor Heating'),
        ('stove', 'Stove (Wood/Coal)'),
        ('electric_heater', 'Electric Heater'),
        ('geothermal', 'Geothermal Heating'),
        ('solar', 'Solar Heating'),
        ('air_conditioner', 'Air Conditioner'),
        ('no_heating', 'No Heating'),
    ]
    WARMING_TYPE_CHOICES_TR = [
        ('natural_gas', 'Doğalgaz'),
        ('central_heating', 'Merkezi Isıtma'),
        ('underfloor_heating', 'Yerden Isıtma'),
        ('stove', 'Soba (Odun/Kömür)'),
        ('electric_heater', 'Elektrikli Isıtıcı'),
        ('geothermal', 'Jeotermal Isıtma'),
        ('solar', 'Güneş Enerjisi ile Isıtma'),
        ('air_conditioner', 'Klima'),
        ('no_heating', 'Isıtma Yok'),
    ]
    warming_type = models.CharField(max_length=50, choices=WARMING_TYPE_CHOICES, blank=True, null=True)
    dues = models.DecimalField(max_digits=50, decimal_places=2, blank=True, null=True)
    dues_currency = models.CharField(max_length=3, choices=CURRENCY_TYPE_CHOICES, default='GBP')
    rent = models.DecimalField(max_digits=50, decimal_places=2, blank=True, null=True)
    rent_currency = models.CharField(max_length=3, choices=CURRENCY_TYPE_CHOICES, default='GBP')
    available_for_loan = models.BooleanField(default=False)
    furnished = models.BooleanField(default=False)
    swap = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class PropertyImage(models.Model):
    id = models.AutoField(primary_key=True)
    property_ad = models.ForeignKey(PropertyAdvertisement, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(
        upload_to='property_images/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])])
    is_cover = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_cover', 'uploaded_at']

    def save(self, *args, **kwargs):
        if self.is_cover:
            PropertyImage.objects.filter(property_ad=self.property_ad, is_cover=True).update(is_cover=False)
        super().save(*args, **kwargs)

    def __str__(self):
        status = " (Cover)" if self.is_cover else ""
        return f"Image for {self.property_ad.title}{status}"


class PropertyExplanation(models.Model):
    id = models.AutoField(primary_key=True)
    property_ad = models.OneToOneField(PropertyAdvertisement, on_delete=models.CASCADE, related_name='explanation')
    explanation = models.TextField()

    def __str__(self):
        return f"Explanation for {self.property_ad.title}"


class PropertyExternalFeature(models.Model):
    id = models.AutoField(primary_key=True)
    property_ad = models.OneToOneField(PropertyAdvertisement, on_delete=models.CASCADE, related_name='external_features')
    elevator = models.BooleanField(default=False)
    gardened = models.BooleanField(default=False)
    fitness = models.BooleanField(default=False)
    security = models.BooleanField(default=False)
    thermal_insulation = models.BooleanField(default=False)
    doorman = models.BooleanField(default=False)
    car_park = models.BooleanField(default=False)
    playground = models.BooleanField(default=False)
    water_tank = models.BooleanField(default=False)
    tennis_court = models.BooleanField(default=False)
    swimming_pool = models.BooleanField(default=False)
    football_field = models.BooleanField(default=False)
    basketball_field = models.BooleanField(default=False)
    generator = models.BooleanField(default=False)
    pvc = models.BooleanField(default=False)
    market = models.BooleanField(default=False)
    siding = models.BooleanField(default=False)
    fire_escape = models.BooleanField(default=False)

    def __str__(self):
        return f"External Features for {self.property_ad.title}"


class PropertyInteriorFeature(models.Model):
    id = models.AutoField(primary_key=True)
    property_ad = models.OneToOneField(PropertyAdvertisement, on_delete=models.CASCADE,
                                       related_name='interior_features')

    adsl = models.BooleanField(default=False)
    alarm = models.BooleanField(default=False)
    balcony = models.BooleanField(default=False)
    built_in_kitchen = models.BooleanField(default=False)
    barbecue = models.BooleanField(default=False)
    furnished = models.BooleanField(default=False)
    laundry_room = models.BooleanField(default=False)
    air_conditioning = models.BooleanField(default=False)
    wallpaper = models.BooleanField(default=False)
    dressing_room = models.BooleanField(default=False)
    jacuzzi = models.BooleanField(default=False)
    tv_satellite = models.BooleanField(default=False)
    laminate = models.BooleanField(default=False)
    marble_floor = models.BooleanField(default=False)
    panel_door = models.BooleanField(default=False)
    blinds = models.BooleanField(default=False)
    shower = models.BooleanField(default=False)
    sauna = models.BooleanField(default=False)
    satin_plaster = models.BooleanField(default=False)
    satin_color = models.BooleanField(default=False)
    ceramic_floor = models.BooleanField(default=False)
    video_intercom = models.BooleanField(default=False)
    parquet = models.BooleanField(default=False)
    spotlight = models.BooleanField(default=False)
    fireplace = models.BooleanField(default=False)
    terrace = models.BooleanField(default=False)
    cloakroom = models.BooleanField(default=False)
    underfloor_heating = models.BooleanField(default=False)
    double_glazing = models.BooleanField(default=False)
    parent_bathroom = models.BooleanField(default=False)

    def __str__(self):
        return f"Interior Features for {self.property_ad.title}"