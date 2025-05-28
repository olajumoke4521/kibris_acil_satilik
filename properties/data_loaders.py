
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
if LOCATION_JSON_FILE_PATH:
        CITY_AREAS_DATA = generate_city_areas_from_json()

CITY_AREAS_MAP = {}
CITY_LABELS_MAP = {}

def _populate_lookup_maps():
    global CITY_AREAS_MAP, CITY_LABELS_MAP, CITY_AREAS_DATA
    if CITY_AREAS_MAP or not CITY_AREAS_DATA:
        return

    for city_entry in CITY_AREAS_DATA:
        city_info = city_entry.get("city", {})
        city_val = city_info.get("value")
        city_label_en = city_info.get("label_en", city_val)

        if not city_val:
            continue

        CITY_LABELS_MAP[city_val.lower()] = city_label_en

        for area_info in city_entry.get("areas", []):
            area_val = area_info.get("value")
            area_label = area_info.get("label", area_val)

            if area_val:
                CITY_AREAS_MAP[(city_val.lower(), area_val.lower())] = {
                    "city_label_en": city_label_en,
                    "area_label": area_label
                }

if CITY_AREAS_DATA:
    _populate_lookup_maps()


def get_location_english_labels(city_value_raw, area_value_raw):
    global CITY_AREAS_MAP, CITY_LABELS_MAP

    if not city_value_raw:
        return {'city_label_en': city_value_raw, 'area_label': area_value_raw}

    cv_lower = city_value_raw.lower()
    av_lower = (area_value_raw or '').lower()

    if (cv_lower, av_lower) in CITY_AREAS_MAP:
        return CITY_AREAS_MAP[(cv_lower, av_lower)]

    city_label_en = CITY_LABELS_MAP.get(cv_lower, city_value_raw)
    area_label_to_return = area_value_raw

    return {'city_label_en': city_label_en, 'area_label': area_label_to_return}