
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
WARMING_TYPE_TR_LABELS_MAP = {
    'natural_gas': 'Doğalgaz',
    'central_heating': 'Merkezi Isıtma',
    'underfloor_heating': 'Yerden Isıtma',
    'stove': 'Soba (Odun/Kömür)',
    'electric_heater': 'Elektrikli Isıtıcı',
    'geothermal': 'Jeotermal Isıtma',
    'solar': 'Güneş Enerjisi ile Isıtma',
    'air_conditioner': 'Klima',
    'no_heating': 'Isıtma Yok'
}

VEHICLE_TYPE_TR_LABELS_MAP = {
    'sedan': 'Sedan',
    'suv': 'SUV',
    'hatchback': 'Heçbek',
    'pickup': 'Pikap',
    'cabrio': 'Kabriyo',
    'minivan': 'Minivan',
}
TRANSMISSION_TR_LABELS_MAP = {
    'automatic': 'Otomatik', 'manual': 'Manuel', 'semi-automatic': 'Yarı Otomatik',
}

FUEL_TYPE_TR_LABELS_MAP = {
    'diesel': 'Dizel', 'gasoline': 'Benzin', 'lpg': 'LPG', 'hybrid': 'Hibrit', 'electric': 'Elektrikli',
}

FEATURE_TR_LABELS_MAP = {
    "Elevator": "Asansör",
    "Gardened": "Bahçeli",
    "Fitness Center": "Spor Salonu",
    "Security": "Güvenlik",
    "Thermal Insulation": "Isı Yalıtımı",
    "Doorman": "Kapıcı",
    "Car Park": "Otopark",
    "Playground": "Çocuk Oyun Alanı",
    "Water Tank": "Su Deposu",
    "Tennis Court": "Tenis Kortu",
    "Swimming Pool": "Yüzme Havuzu",
    "Football Field": "Futbol Sahası",
    "Basketball Field": "Basketbol Sahası",
    "Generator": "Jeneratör",
    "PVC": "PVC Doğrama",
    "Market Nearby": "Market Yakınında",
    "Siding": "Dış Cephe Kaplaması",
    "Fire Escape": "Yangın Merdiveni",

    "ADSL": "ADSL",
    "Alarm System": "Alarm Sistemi",
    "Balcony": "Balkon",
    "Built-in Kitchen": "Ankastre Mutfak",
    "Barbecue": "Barbekü",
    "Laundry Room": "Çamaşır Odası",
    "Air Conditioning": "Klima",
    "Wallpaper": "Duvar Kağıdı",
    "Dressing Room": "Giyinme Odası",
    "Jacuzzi": "Jakuzi",
    "TV Satellite": "Uydu TV",
    "Laminate Flooring": "Laminat Parke",
    "Marble Floor": "Mermer Zemin",
    "Panel Door": "Panel Kapı",
    "Blinds": "Panjur",
    "Shower Cabin": "Duşakabin",
    "Sauna": "Sauna",
    "Satin Plaster": "Saten Alçı",
    "Satin Paint": "Saten Boya",
    "Ceramic Floor": "Seramik Zemin",
    "Video Intercom": "Görüntülü Diafon",
    "Parquet Flooring": "Parke Zemin",
    "Spotlight": "Spot Aydınlatma",
    "Fireplace": "Şömine",
    "Terrace": "Teras",
    "Cloakroom": "Vestiyer",
    "Underfloor Heating": "Yerden Isıtma",
    "Double Glazing": "Çift Cam",
    "Parent Bathroom": "Ebeveyn Banyosu",

    "Fabric Armchair": "Kumaş Koltuk",
    "Leather-Fabric Armchair": "Deri-Kumaş Koltuk",
    "Electric Windshields": "Elektrikli Ön Camlar",
    "Front Armrest": "Ön Kol Dayama",
    "Rear Armrest": "Arka Kol Dayama",
    "Keyless Drive": "Anahtarsız Çalıştırma",
    "Forward Gear": "İleri Dişli",
    "Hydraulic Steering": "Hidrolik Direksiyon",
    "Functional Steering Wheel": "Fonksiyonel Direksiyon",
    "Adjustable Steering Wheel": "Ayarlanabilir Direksiyon",
    "Leather Steering Wheel": "Deri Direksiyon",
    "Cruise Control": "Hız Sabitleyici",
    "Adaptive Cruise Control": "Adaptif Hız Sabitleyici",
    "Reverse View Camera": "Geri Görüş Kamerası",
    "Road Computer": "Yol Bilgisayarı",
    "Start-Stop System": "Start-Stop Sistemi",
    "Digital Air Conditioner": "Dijital Klima",
    "Digital Monitor": "Dijital Ekran",

    "Xenon Headlamps": "Xenon Farlar",
    "Adaptive Headlights": "Adaptif Farlar",
    "Headlight Sensor": "Far Sensörü",
    "Electric Mirrors": "Elektrikli Aynalar",
    "Folding Mirrors": "Katlanır Aynalar",
    "Heated Mirrors": "Isıtmalı Aynalar",
    "Rear Parking Sensor": "Arka Park Sensörü",
    "Front Parking Sensor": "Ön Park Sensörü",
    "Rain Sensor": "Yağmur Sensörü",
    "Alloy Wheels": "Alaşım Jant",
    "Rear Window Defroster": "Arka Cam Buz Çözücü",
    "Smart Tailgate": "Akıllı Bagaj Kapağı",
}
