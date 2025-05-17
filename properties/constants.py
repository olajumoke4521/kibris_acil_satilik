import os
from django.conf import settings

LOCATION_JSON_FILE_PATH = os.path.join(settings.BASE_DIR,  'location.json')

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

PROPERTY_TYPE_TR_LABELS_MAP = {
    'villa': 'Villa', 'apartment': 'Apartman',
        'residence': 'Rezidans',
        'twin_villa' : 'İkiz Villa',
        'penthouse': 'Çatı katı',
        'bungalow': 'Bungalov',
        'family_house': 'Aile Evleri',
        'complete_building': 'Eksiksiz Bina',
        'timeshare': 'Devremülk',
        'abandoned_building': 'Terkedilmiş Bina',
        'half_construction': 'Yarım İnşaat'
}
VEHICLE_TYPE_TR_LABELS_MAP = {
    'sedan': 'Sedan',
    'suv': 'SUV',
    'hatchback': 'Heçbek',
    'pickup': 'Pikap',
    'cabrio': 'Kabriyo',
    'minivan': 'Minivan',
}
