from django_filters import rest_framework as filters
from .models import CarAdvertisement


PREDEFINED_CAR_DATA = {
    "BMW": {
        "series": ["1 Series", "2 Series", "3 Series", "4 Series", "5 Series", "7 Series", "X1", "X2", "X3", "X4", "X5", "X6", "X7", "Z4", "M Series"],
    },
    "Mercedes-Benz": {
        "series": ["A-Class", "C-Class", "E-Class", "S-Class", "CLA", "CLS", "GLA", "GLB", "GLC", "GLE", "GLS", "G-Class", "AMG GT"]
    },
    "Audi": {
        "series": ["A1", "A3", "A4", "A5", "A6", "A7", "A8", "Q2", "Q3", "Q5", "Q7", "Q8", "TT", "R8", "e-tron"]
    },
    "Volkswagen": {
        "series": ["Polo", "Golf", "Passat", "Tiguan", "T-Roc", "Touareg", "Arteon", "ID.3", "ID.4"]
    },
    "Toyota": {
        "series": ["Yaris", "Corolla", "Camry", "RAV4", "C-HR", "Hilux", "Land Cruiser", "Supra", "Prius"]
    },
    "Honda": {
        "series": ["Jazz", "Civic", "HR-V", "CR-V", "NSX"]
    },
    "Ford": {
        "series": ["Fiesta", "Focus", "Mondeo", "Puma", "Kuga", "Mustang", "Ranger"]
    },
    "Hyundai": {
        "series": ["i10", "i20", "i30", "Elantra", "Tucson", "Santa Fe", "Kona"]
    },
    "Kia": {
        "series": ["Picanto", "Rio", "Ceed", "Sportage", "Sorento", "Stonic"]
    },
    "Nissan": {
        "series": ["Micra", "Juke", "Qashqai", "X-Trail", "Navara", "GT-R"]
    },
    "Peugeot": {
        "series": ["208", "308", "508", "2008", "3008", "5008"]
    },
    "Renault": {
        "series": ["Clio", "Megane", "Captur", "Kadjar"]
    },
    "Skoda": {
        "series": ["Fabia", "Octavia", "Superb", "Kamiq", "Karoq", "Kodiaq"]
    },
    "Volvo": {
        "series": ["XC40", "XC60", "XC90", "S60", "S90", "V60", "V90"]
    }
}

class CarFilter(filters.FilterSet):
    minPrice = filters.NumberFilter(field_name="price", lookup_expr='gte')
    maxPrice = filters.NumberFilter(field_name="price", lookup_expr='lte')
    type = filters.CharFilter(field_name="vehicle_type", lookup_expr='iexact')
    brand = filters.CharFilter(field_name="brand",
                                  lookup_expr='iexact')
    series = filters.CharFilter(method='filter_by_series_text')
    modelYear = filters.NumberFilter(field_name="model_year")

    class Meta:
        model = CarAdvertisement
        fields = {
            'price': ['gte', 'lte'],
            'vehicle_type': ['iexact'],
            'brand': ['iexact'],
            'model_year': ['exact'],
        }

    def filter_by_series_text(self, queryset, name, value):

        series_label_to_search = None

        for brand_name_key, brand_detail in PREDEFINED_CAR_DATA.items():
            for series_display_name in brand_detail.get("series", []):
                generated_series_value = series_display_name.lower().replace(" ", "-")
                if generated_series_value == value:
                    series_label_to_search = series_display_name
                    break
            if series_label_to_search:
                break

        if series_label_to_search:

            return queryset.filter(model__icontains=series_label_to_search)

        return queryset