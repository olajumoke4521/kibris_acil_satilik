
from django.db import models
from django.db.models.fields.reverse_related import (
    ManyToOneRel,
    OneToOneRel,
    ManyToManyRel
)
from django.apps import apps

def get_frontend_field_type(field):
    if field.choices:
        return 'select'
    if isinstance(field, models.ImageField):
        return 'image upload'
    if isinstance(field, models.TextField):
        if field.model == apps.get_model('vehicles', 'CarExplanation') and field.name == 'explanation':
            return 'string'
        return 'textarea'

    return 'unknown'


def get_model_form_schema(model_class, is_child_schema=False, field_instance_on_parent=None):
    schema_dict = {}

    excluded_base_fields = {'id'} if not is_child_schema else {}
    fields_to_skip_in_children = {'car_ad'}

    NESTED_OBJECT_RELATIONS = {
        'internal_features': apps.get_model('vehicles', 'CarInternalFeature'),
        'external_features': apps.get_model('vehicles', 'CarExternalFeature'),
    }
    LIST_CHILD_RELATIONS = {
        'images': apps.get_model('vehicles', 'CarImage'),
    }

    for field in model_class._meta.get_fields(include_hidden=True):

        if is_child_schema and field.name in fields_to_skip_in_children:
            continue
        if field.name in excluded_base_fields and not is_child_schema:
            if not (model_class == apps.get_model('vehicles',
                                                  'CarAdvertisement') and field.name == 'id'):
                continue

        if is_child_schema and field.primary_key and field.name == 'id' and \
                not (model_class == apps.get_model('vehicles', 'CarImage') and field.name == 'id'):
            continue

        field_data = {}
        field_name = field.name

        if field_name in NESTED_OBJECT_RELATIONS and \
                isinstance(field, OneToOneRel) and \
                field.related_model == NESTED_OBJECT_RELATIONS[field_name]:
            related_model_class = field.related_model
            field_data = {
                'type': 'nested object',
                'required': False,
                'read_only': True,
                'label': str(related_model_class._meta.verbose_name).capitalize(),
                'children': get_model_form_schema(related_model_class, is_child_schema=True,
                                                     field_instance_on_parent=field)
            }
            schema_dict[field_name] = field_data
            continue

        elif field_name in LIST_CHILD_RELATIONS and \
                isinstance(field, (ManyToOneRel, ManyToManyRel)) and \
                field.related_model == LIST_CHILD_RELATIONS[field_name]:
            related_model_class = field.related_model
            field_data = {
                'type': 'field',
                'required': False,
                'read_only': True,
                'label': str(related_model_class._meta.verbose_name_plural).capitalize(),
                'child': {
                    'type': 'nested object',
                    'required': False,
                    'read_only': True,
                    'children': get_model_form_schema(related_model_class, is_child_schema=True,
                                                         field_instance_on_parent=field)
                }
            }
            schema_dict[field_name] = field_data
            continue

        elif model_class == apps.get_model('vehicles', 'CarAdvertisement') and \
                field_name == 'explanation' and \
                isinstance(field, OneToOneRel) and \
                field.related_model == apps.get_model('vehicles', 'CarExplanation'):

            explanation_model_actual = apps.get_model('vehicles', 'CarExplanation')
            try:
                explanation_text_field_on_related_model = explanation_model_actual._meta.get_field('explanation')
            except models.FieldDoesNotExist:
                continue

            field_data = {
                'label': str(explanation_text_field_on_related_model.verbose_name).capitalize(),
                'type': get_frontend_field_type(explanation_text_field_on_related_model),
                'required': not explanation_text_field_on_related_model.blank,
                'read_only': False,
                'help_text': str(
                    explanation_text_field_on_related_model.help_text) if explanation_text_field_on_related_model.help_text else ""
            }
            if hasattr(explanation_text_field_on_related_model,
                       'max_length') and explanation_text_field_on_related_model.max_length is not None:
                field_data['max_length'] = explanation_text_field_on_related_model.max_length

            schema_dict[field_name] = field_data
            continue


        if isinstance(field, (OneToOneRel, ManyToOneRel, ManyToManyRel)):
            continue

        if not field.concrete and not field.many_to_many:
            if not (model_class == apps.get_model('vehicles', 'CarImage') and field_name == 'image_url'):
                continue

        if model_class == apps.get_model('vehicles', 'CarAdvertisement') and field_name == 'id' and \
                field.primary_key and not is_child_schema:

            field_data = {
                'type': get_frontend_field_type(field),
                'required': False,
                'read_only': True,
                'label': str(field.verbose_name).capitalize(),
            }

        elif model_class == apps.get_model('vehicles', 'CarImage') and field_name == 'image_url':
            field_data = {
                'type': 'field',
                'required': False,
                'read_only': True,
                'label': 'Image url'
            }
        elif hasattr(field, 'verbose_name'):
            field_data = {
                'type': get_frontend_field_type(field),
                'required': not field.blank if hasattr(field, 'blank') else (
                    not field.null if is_child_schema else True),
                'read_only': not field.editable if hasattr(field, 'editable') else False,
                'label': str(field.verbose_name).capitalize(),
            }

            # For child 'id' fields like CarImage.id
            if is_child_schema and field.primary_key and field.name == 'id':
                field_data['read_only'] = True

            if hasattr(field, 'help_text') and field.help_text:
                field_data['help_text'] = str(field.help_text)

            if hasattr(field, 'default') and field.default is not models.NOT_PROVIDED:
                field_data['default'] = field.default

            if hasattr(field, 'max_length') and field.max_length is not None:
                field_data['max_length'] = field.max_length

            if isinstance(field, models.DecimalField):
                field_data['max_digits'] = field.max_digits
                field_data['decimal_places'] = field.decimal_places

            if isinstance(field, models.ForeignKey):
                field_data['related_model'] = field.related_model.__name__

            if field.choices:
                if field_name == 'series' and model_class.__name__ == 'CarAdvertisement':
                    field_data['type'] = 'dependent_select'
                    field_data['dependent_on'] = 'brand'
                    field_data['source_data_key'] = 'brand_series_map'
                    field_data['choices'] = []
                else:
                    field_data['choices'] = []
                    actual_choices_tr_attr_name = None
                    candidate_name_field = f"{field.name.upper()}_CHOICES_TR"
                    candidate_name_attname = f"{field.attname.upper()}_CHOICES_TR"
                    if hasattr(model_class, candidate_name_field):
                        actual_choices_tr_attr_name = candidate_name_field
                    elif hasattr(model_class, candidate_name_attname):
                        actual_choices_tr_attr_name = candidate_name_attname

                    choices_tr_list = None
                    if actual_choices_tr_attr_name: choices_tr_list = getattr(model_class, actual_choices_tr_attr_name,
                                                                              None)

                    tr_choices_map = dict(choices_tr_list) if choices_tr_list else {}
                    for value, label_en in field.choices:
                        field_data['choices'].append({
                            'value': value, 'label': str(label_en),
                            'label_tr': str(tr_choices_map.get(value, label_en))
                        })

        if field_data:
            schema_dict[field_name] = field_data

    if is_child_schema:
        return schema_dict
    else:
        return schema_dict


from properties.constants import PREDEFINED_CAR_DATA

BRAND_SLUG_TO_DISPLAY_LOOKUP = {
    brand.lower().replace(" ", "-"): brand
    for brand in PREDEFINED_CAR_DATA.keys()
}

SERIES_SLUG_TO_DISPLAY_LOOKUP = {}
for brand_details in PREDEFINED_CAR_DATA.values():
    for series_name_item in brand_details.get("series", []):
        actual_series_name = ""
        if isinstance(series_name_item, str):
            actual_series_name = series_name_item
        elif isinstance(series_name_item, dict) and 'name' in series_name_item:
            actual_series_name = series_name_item['name']

        if actual_series_name:
            series_slug = actual_series_name.lower().replace(" ", "-")
            if series_slug not in SERIES_SLUG_TO_DISPLAY_LOOKUP:
                SERIES_SLUG_TO_DISPLAY_LOOKUP[series_slug] = actual_series_name


def get_brand_display_name(brand_slug_value):
    return BRAND_SLUG_TO_DISPLAY_LOOKUP.get(brand_slug_value, brand_slug_value)


def get_series_display_name(series_slug_value):
    return SERIES_SLUG_TO_DISPLAY_LOOKUP.get(series_slug_value, series_slug_value)