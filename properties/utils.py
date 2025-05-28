from django.core.files.base import ContentFile
from django.db import models
from django.db.models.fields.reverse_related import (
    ManyToOneRel,
    OneToOneRel,
    ManyToManyRel
)
from django.apps import apps
from django.conf import settings
import base64
import uuid

from properties.constants import FEATURE_TR_LABELS_MAP


def base64_to_image_file(base64_string, name_prefix="img_"):
    """
    Converts a base64 string (possibly a data URI) to a Django ContentFile.
    """
    if not base64_string or not isinstance(base64_string, str):
        return None

    try:
        if ';base64,' in base64_string:
            header, base64_data = base64_string.split(';base64,', 1)
            if 'data:' in header:
                mime_type = header.split('data:', 1)[1].split(';')[0]
            else:
                mime_type = ''
        else:
            base64_data = base64_string
            mime_type = '' # No mime type info available

        ext = 'bin' # Default extension
        if mime_type:
            mime_map = {
                'image/jpeg': 'jpg',
                'image/png': 'png',
                'image/gif': 'gif',
                'image/webp': 'webp',
                'image/avif': 'avif',
                'image/svg+xml': 'svg',
            }
            ext = mime_map.get(mime_type.lower(), mime_type.split('/')[-1] if '/' in mime_type else 'bin')
            ext = ''.join(filter(str.isalnum, ext))[:5] if ext else 'bin'
            if not ext: ext = 'bin'
        elif len(base64_data) % 4 == 0 :
            ext = 'png'

        decoded_file = base64.b64decode(base64_data)
        file_name = f"{name_prefix}{uuid.uuid4()}.{ext}"
        return ContentFile(decoded_file, name=file_name)
    except Exception:
        return None


def get_bilingual_feature_metadata(model_class):
    features = {}
    for field in model_class._meta.get_fields():
        if isinstance(field, models.BooleanField):
            english_label = field.verbose_name.string if hasattr(field.verbose_name, 'string') else str(
                field.verbose_name)

            turkish_label = FEATURE_TR_LABELS_MAP.get(english_label, english_label)

            features[field.name] = {
                'label_en': english_label,
                'label_tr': turkish_label
            }
    return features


def get_choices_as_list_of_dicts(choices_tuple):
    """Helper function to convert Django choices tuple to a list of dicts."""
    return [{"value": choice[0], "label": choice[1]} for choice in choices_tuple]


def get_bilingual_choices_as_list_of_dicts(choices_tuple, tr_label_map=None, en_label_map=None):
    bilingual_list = []
    for value, default_label in choices_tuple:
        if tr_label_map and isinstance(tr_label_map, dict) and value in tr_label_map:
            label_tr = tr_label_map[value]
        else:
            label_tr = default_label

        if en_label_map and isinstance(en_label_map, dict) and value in en_label_map:
            label_en = en_label_map[value]
        else:
            label_en = default_label

        bilingual_list.append({
            "value": value,
            "label_tr": label_tr,
            "label_en": label_en
        })
    return bilingual_list

def get_frontend_field_type(field):
    if field.choices:
        return 'select'
    if isinstance(field, models.BooleanField):
        return 'boolean'
    if isinstance(field, (models.IntegerField, models.AutoField)):
        return 'integer'
    if isinstance(field, (models.DecimalField, models.FloatField)):
        return 'number'
    if isinstance(field, models.EmailField):
        return 'email'
    if isinstance(field, models.URLField):
        return 'url'
    if isinstance(field, models.DateField):
        return 'date'
    if isinstance(field, models.DateTimeField):
        return 'datetime'
    if isinstance(field, models.TimeField):
        return 'time'
    if isinstance(field, models.ImageField):
        return 'image upload'
    if isinstance(field, models.FileField):
        return 'file'
    if isinstance(field, models.TextField):
        return 'textarea'
    if isinstance(field, models.CharField):
        return 'text'
    if isinstance(field, models.ForeignKey):

        if field.related_model == apps.get_model(settings.LOCATION_MODEL_APP_LABEL,
                                                 'Location'):  #
            return 'location_select'
        return 'foreignkey'
    if isinstance(field, models.OneToOneField):
        return 'onetoone_relation'
    if isinstance(field, models.ManyToManyField):
        return 'manytomany_relation'
    return 'unknown'

def get_dynamic_model_form_schema(
        model_class,
        app_label,
        nested_object_relations_config=None,
        list_child_relations_config=None,
        single_field_one_to_one_config=None,
        special_handlers=None,
        is_child_schema=False,
        field_instance_on_parent=None
):
    schema_dict = {}

    nested_object_relations_config = nested_object_relations_config or {}
    list_child_relations_config = list_child_relations_config or {}
    single_field_one_to_one_config = single_field_one_to_one_config or {}
    special_handlers = special_handlers or {}

    fields_to_skip_in_children = {'property_ad', 'car_ad'}
    excluded_top_level_only = {'id'} if not is_child_schema else set()

    for field in model_class._meta.get_fields(include_hidden=True):
        field_name = field.name
        field_data = {}


        if is_child_schema:
            if field_name in fields_to_skip_in_children:
                continue
            if field.primary_key and field_name == 'id':

                is_image_model_id = False
                for rel_name, img_model_name_from_config in list_child_relations_config.items():
                    if isinstance(img_model_name_from_config, str):
                        try:
                            if field.model == apps.get_model(app_label, img_model_name_from_config):
                                is_image_model_id = True
                                break
                        except LookupError:
                            pass
                if not is_image_model_id:
                    continue


        if field_name in nested_object_relations_config and isinstance(field, OneToOneRel):
            related_model_name = nested_object_relations_config[field_name]
            try:
                related_model_class = apps.get_model(app_label, related_model_name)
                if field.related_model == related_model_class:
                    field_data = {
                        'type': 'nested object', 'required': False, 'read_only': True,
                        'label': str(
                            getattr(field, 'verbose_name', related_model_class._meta.verbose_name)).capitalize(),
                        'children': get_dynamic_model_form_schema(related_model_class, app_label,
                                                                  nested_object_relations_config,
                                                                  list_child_relations_config,
                                                                  single_field_one_to_one_config, special_handlers,
                                                                  is_child_schema=True, field_instance_on_parent=field)
                    }
                    schema_dict[field_name] = field_data
                    continue
            except LookupError:
                print(f"LookupError for B1: {app_label}.{related_model_name}"); pass

        elif field_name in list_child_relations_config and isinstance(field, (ManyToOneRel, ManyToManyRel)):
            related_model_name = list_child_relations_config[field_name]
            try:
                related_model_class = apps.get_model(app_label, related_model_name)
                if field.related_model == related_model_class:
                    field_data = {
                        'type': 'field', 'required': False, 'read_only': True,
                        'label': str(
                            getattr(field, 'verbose_name', related_model_class._meta.verbose_name_plural)).capitalize(),
                        'child': {
                            'type': 'nested object', 'required': False, 'read_only': True,
                            'children': get_dynamic_model_form_schema(related_model_class, app_label,
                                                                      nested_object_relations_config,
                                                                      list_child_relations_config,
                                                                      single_field_one_to_one_config, special_handlers,
                                                                      is_child_schema=True,
                                                                      field_instance_on_parent=field)
                        }
                    }
                    schema_dict[field_name] = field_data
                    continue
            except LookupError:
                print(f"LookupError for B2: {app_label}.{related_model_name}"); pass

        elif field_name in single_field_one_to_one_config and isinstance(field, OneToOneRel):
            related_model_name, text_field_name = single_field_one_to_one_config[field_name]
            try:
                related_model_class = apps.get_model(app_label, related_model_name)
                if field.related_model == related_model_class:
                    text_field_on_related = related_model_class._meta.get_field(text_field_name)
                    custom_type_override = 'string' if field_name == 'explanation' else None
                    field_data = {
                        'label': str(text_field_on_related.verbose_name).capitalize(),
                        'type': custom_type_override or get_frontend_field_type(text_field_on_related),
                        'required': not text_field_on_related.blank, 'read_only': False,
                        'help_text': str(text_field_on_related.help_text) if text_field_on_related.help_text else ""
                    }
                    if hasattr(text_field_on_related, 'max_length') and text_field_on_related.max_length is not None:
                        field_data['max_length'] = text_field_on_related.max_length
                    schema_dict[field_name] = field_data
                    continue
            except (LookupError, models.FieldDoesNotExist):
                print(f"Error for B3: {field_name}"); pass

        if isinstance(field, (OneToOneRel, ManyToOneRel, ManyToManyRel)):
            continue


        if field_name in special_handlers:
            handler_config = special_handlers[field_name]
            if field.name == handler_config.get("field_name_match", field_name):
                if handler_config["type"] == "dependent_pair" and field_name == "series":
                    field_data = {
                        'label': str(field.verbose_name).capitalize(), 'type': 'dependent_select',
                        'dependent_on': handler_config['depends_on'], 'source_data_key': handler_config['source_key'],
                        'required': not field.blank, 'choices': []
                    }
                    schema_dict[field_name] = field_data
                    continue
                elif handler_config["type"] == "location_picker":
                    location_app_label = handler_config.get('related_model_app', app_label)
                    if isinstance(field, models.ForeignKey) and field.related_model == apps.get_model(
                            location_app_label, handler_config['related_model_name']):
                        field_data = {
                            'label': str(field.verbose_name).capitalize(), 'type': 'location_picker',
                            'required': not field.blank, 'city_source_key': handler_config['city_source_key'],
                            'area_source_key': handler_config['area_source_key'],
                            'city_payload_key': handler_config.get('city_payload_key', 'city'),
                            'area_payload_key': handler_config.get('area_payload_key', 'area'),
                        }
                        schema_dict[field_name] = field_data
                        continue

        is_main_model_auto_pk = (
                    field.model == model_class and field.primary_key and field.auto_created and not is_child_schema)

        if (field.concrete or field.many_to_many) and hasattr(field, 'verbose_name') and not is_main_model_auto_pk:
            if field.model == model_class and field_name == 'id' and field.primary_key and not is_child_schema:
                field_data = {
                    'type': get_frontend_field_type(field), 'required': False, 'read_only': True,
                    'label': str(field.verbose_name).capitalize(),
                }

            elif list_child_relations_config and field.name == 'image_url':
                is_synthetic_image_url = False
                for rel_name, img_model_name_from_config in list_child_relations_config.items():
                    if isinstance(img_model_name_from_config, str):
                        try:
                            if field.model == apps.get_model(app_label, img_model_name_from_config):
                                is_synthetic_image_url = True
                                break
                        except LookupError:
                            pass
                if is_synthetic_image_url:
                    field_data = {'type': 'field', 'required': False, 'read_only': True, 'label': 'Image url'}
                else:
                    pass

            else:
                field_data = {
                    'type': get_frontend_field_type(field),
                    'required': not field.blank if hasattr(field, 'blank') else (
                        not field.null if is_child_schema else True),
                    'read_only': (not field.editable if hasattr(field, 'editable') else False) or \
                                 (field.primary_key and is_child_schema),
                    'label': str(field.verbose_name).capitalize(),
                }
                if hasattr(field, 'help_text') and field.help_text: field_data['help_text'] = str(field.help_text)
                if hasattr(field, 'default') and field.default is not models.NOT_PROVIDED: field_data[
                    'default'] = field.default
                if hasattr(field, 'max_length') and field.max_length is not None: field_data[
                    'max_length'] = field.max_length
                if isinstance(field, models.DecimalField):
                    field_data['max_digits'] = field.max_digits
                    field_data['decimal_places'] = field.decimal_places

                if isinstance(field, models.ForeignKey):
                    is_special_fk = field_name in special_handlers and \
                                    special_handlers[field_name]["type"] == "location_picker" and \
                                    field.name == special_handlers[field_name].get("field_name_match", field_name)
                    if not is_special_fk:
                        field_data['related_model'] = field.related_model.__name__

                if field.choices:
                    is_brand_field = field_name == 'brand' and 'series' in special_handlers and \
                                     special_handlers['series']['type'] == 'dependent_pair'
                    is_series_field_already_handled = field_name == 'series' and field_name in special_handlers and \
                                                      special_handlers[field_name]['type'] == 'dependent_pair'

                    if not is_series_field_already_handled:
                        field_data['choices'] = []
                        choices_tr_list = None

                        model_for_choices_tr = field.model
                        if hasattr(model_for_choices_tr, f"{field.name.upper()}_CHOICES_TR"):
                            choices_tr_list = getattr(model_for_choices_tr, f"{field.name.upper()}_CHOICES_TR", None)
                        elif hasattr(model_for_choices_tr, f"{field.attname.upper()}_CHOICES_TR"):
                            choices_tr_list = getattr(model_for_choices_tr, f"{field.attname.upper()}_CHOICES_TR", None)

                        tr_choices_map = dict(choices_tr_list) if choices_tr_list else {}
                        for value, label_en_choice in field.choices:
                            field_data['choices'].append({
                                'value': value, 'label': str(label_en_choice),
                                'label_tr': str(tr_choices_map.get(value, label_en_choice))
                            })

            if field_data:
                schema_dict[field_name] = field_data


    if is_child_schema:
        return schema_dict
    else:
        if 'id' not in schema_dict and hasattr(model_class._meta, 'pk') and model_class._meta.pk.name == 'id':
            pk_field = model_class._meta.pk
            schema_dict['id'] = {
                'type': get_frontend_field_type(pk_field), 'required': False, 'read_only': True,
                'label': str(pk_field.verbose_name).capitalize(),
            }
        return schema_dict