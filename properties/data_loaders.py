
import json
from pathlib import Path
from django.conf import settings

_target_file_name = 'locations.json'
_project_root_dir = Path(settings.BASE_DIR)
LOCATION_JSON_FILE_PATH = None
_possible_paths = [
    _project_root_dir / 'data' / _target_file_name,
    _project_root_dir / _target_file_name,
]
for _p in _possible_paths:
    if _p.exists() and _p.is_file():
        LOCATION_JSON_FILE_PATH = _p
        print(f"[[ DATA_LOADERS.PY ]] Location JSON file will be loaded from: {LOCATION_JSON_FILE_PATH}")
        break

if not LOCATION_JSON_FILE_PATH:
    print(
        f"[[ DATA_LOADERS.PY - ERROR ]] Location JSON file ('{_target_file_name}') not found. CITY_AREAS_DATA will be empty.")



def generate_city_areas_from_json():
    print("\n" + "-" * 60)
    print(f"  [[ generate_city_areas_from_json() CALLED ]]")

    if not LOCATION_JSON_FILE_PATH:
        print(f"    ERROR: LOCATION_JSON_FILE_PATH is not set. Cannot load locations.")
        print(f"  [[ generate_city_areas_from_json() RETURNING EMPTY LIST ]]")
        print("-" * 60 + "\n")
        return []

    try:
        with open(LOCATION_JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            raw_locations = json.load(f)
        print(f"    SUCCESS: Loaded {len(raw_locations)} raw entries from {LOCATION_JSON_FILE_PATH}")
    except FileNotFoundError:
        print(f"    ERROR: Location JSON file not found at {LOCATION_JSON_FILE_PATH} (inside function)")
        print(f"  [[ generate_city_areas_from_json() RETURNING EMPTY LIST ]]")
        print("-" * 60 + "\n")
        return []
    except json.JSONDecodeError:
        print(f"    ERROR: Could not decode JSON from {LOCATION_JSON_FILE_PATH} (inside function)")
        print(f"  [[ generate_city_areas_from_json() RETURNING EMPTY LIST ]]")
        print("-" * 60 + "\n")
        return []
    except Exception as e:
        print(f"    ERROR: Unexpected error loading JSON {LOCATION_JSON_FILE_PATH}: {e}")
        print(f"  [[ generate_city_areas_from_json() RETURNING EMPTY LIST ]]")
        print("-" * 60 + "\n")
        return []

    grouped_by_province_value = {}
    items_processed_count = 0

    for loc_idx, loc in enumerate(raw_locations):
        if not isinstance(loc, dict):
            print(f"    WARNING: Raw location item at index {loc_idx} is not a dict: {loc}")
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

    print(f"    Processed {items_processed_count} raw location entries into groups.")
    print(f"    Number of unique provinces grouped: {len(grouped_by_province_value)}")

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

    print(f"    Generated final_city_areas_data with {len(final_city_areas_data)} cities.")
    if final_city_areas_data:
        print(f"    Sample of first city in final_city_areas_data: {str(final_city_areas_data[0])[:200]}...")

    print(f"  [[ generate_city_areas_from_json() FINISHED ]]")
    print("-" * 60 + "\n")
    return final_city_areas_data



print("\n" + "=" * 80)
print(f"[[ DATA_LOADERS.PY - GLOBAL VARIABLE ASSIGNMENT ]]")
CITY_AREAS_DATA = []
try:
    if LOCATION_JSON_FILE_PATH:
        print(f"  Calling generate_city_areas_from_json() to populate CITY_AREAS_DATA...")
        CITY_AREAS_DATA = generate_city_areas_from_json()
    else:
        print(f"  Skipping CITY_AREAS_DATA population as LOCATION_JSON_FILE_PATH is not set.")

    print(f"  CITY_AREAS_DATA populated. Number of cities: {len(CITY_AREAS_DATA)}")
    if CITY_AREAS_DATA and len(CITY_AREAS_DATA) < 3:
        print(f"  Sample of CITY_AREAS_DATA: {CITY_AREAS_DATA[:3]}")
    elif CITY_AREAS_DATA:
        print(f"  Sample of first city in CITY_AREAS_DATA: {CITY_AREAS_DATA[0]}")

except Exception as e:
    print(f"  [[ ERROR DURING GLOBAL VARIABLE ASSIGNMENT ]]: {e}")
    import traceback

    traceback.print_exc()

print(f"[[ DATA_LOADERS.PY - MODULE INITIALIZATION COMPLETE ]]")
print(f"  Final CITY_AREAS_DATA has {len(CITY_AREAS_DATA)} entries.")
print("=" * 80 + "\n")