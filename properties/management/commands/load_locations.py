import json
from django.core.management.base import BaseCommand
from properties.models import Location


class Command(BaseCommand):
    help = 'Loads location data from a JSON file into the Location model'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='The JSON file path to load data from')

    def handle(self, *args, **options):
        json_file_path = options['json_file']
        self.stdout.write(self.style.SUCCESS(f"Loading locations from {json_file_path}"))

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                locations_data = json.load(f)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {json_file_path}"))
            return
        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR(f"Error decoding JSON from file: {json_file_path}"))
            return

        created_count = 0
        skipped_count = 0

        for loc_data in locations_data:
            province = loc_data.get('province')
            district = loc_data.get('district')  # This can be None if not in JSON
            # neighborhood = loc_data.get('neighborhood') # If you add neighborhoods to JSON

            if not province:
                self.stdout.write(self.style.WARNING(f"Skipping entry with no province: {loc_data}"))
                skipped_count += 1
                continue

            # Using get_or_create to avoid duplicates based on your unique_together constraint
            # Adjust fields in defaults and for query based on your model
            location_obj, created = Location.objects.get_or_create(
                province=province,
                district=district,  # Pass None if district is not provided or should be null
                # neighborhood=neighborhood, # if you use it
                defaults={
                    'province': province,
                    'district': district,
                    # 'neighborhood': neighborhood
                }
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Successfully created: {location_obj}"))
            else:
                skipped_count += 1
                self.stdout.write(self.style.NOTICE(f"Skipped (already exists): {location_obj}"))

        self.stdout.write(self.style.SUCCESS(
            f"Finished loading locations. Created: {created_count}, Skipped (already existed): {skipped_count}"))