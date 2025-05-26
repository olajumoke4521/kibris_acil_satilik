
import json
from pathlib import Path
from django.conf import settings

_target_file_name = 'location.json'
_project_root_dir = Path(settings.BASE_DIR)
LOCATION_JSON_FILE_PATH =  _project_root_dir / _target_file_name

def generate_city_areas_from_json():
    try:
        with open(LOCATION_JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            raw_locations = json.load(f)
    except Exception as e:
        return []

    grouped_by_province_value = {}
    items_processed_count = 0

    for loc_idx, loc in enumerate(raw_locations):
        if not isinstance(loc, dict):
            continue

        province_val = loc.get("province_value")
        province_l_tr = loc.get("province_label_tr")
        province_l_en = loc.get("province_label_en")
        district_name = loc.get("district")

        if not province_val or not district_name:
            print(f"    WARNING: Raw location item at index {loc_idx} missing province_value or district: {loc}")
            continue

        if province_val not in grouped_by_province_value:
            grouped_by_province_value[province_val] = {
                "city": {
                    "value": province_val,
                    "label_tr": province_l_tr or province_val,
                    "label_en": province_l_en or province_val
                },
                "areas_temp_list": []
            }


        district_filter_value = district_name.lower().replace(" ", "-").replace("(", "").replace(")", "")
        area_object = {
            "value": district_filter_value,
            "label": district_name
        }

        grouped_by_province_value[province_val]["areas_temp_list"].append(area_object)
        items_processed_count += 1

    final_city_areas_data = []
    for province_value_key, city_data_group in grouped_by_province_value.items():
        unique_areas = []
        seen_area_values = set()
        sorted_areas = sorted(city_data_group["areas_temp_list"], key=lambda x: x.get('label', ''))

        for area in sorted_areas:
            area_val = area.get("value")
            if area_val not in seen_area_values:
                unique_areas.append(area)
                seen_area_values.add(area_val)

        final_city_areas_data.append({
            "city": city_data_group["city"],
            "areas": unique_areas
        })

    final_city_areas_data.sort(key=lambda x: x.get('city', {}).get('label_tr', ''))

    return final_city_areas_data


CITY_AREAS_DATA = []
try:
    if LOCATION_JSON_FILE_PATH:
        CITY_AREAS_DATA = generate_city_areas_from_json()
    else:
        print(f"  Skipping CITY_AREAS_DATA population as LOCATION_JSON_FILE_PATH is not set.")

except Exception as e:
    print(f"  [[ ERROR DURING GLOBAL VARIABLE ASSIGNMENT ]]: {e}")
