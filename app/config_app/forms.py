import json
from typing import Optional, Literal, Type, List, Union, Tuple, Dict

from django import forms
from django.forms.widgets import Input
from django.db import models
from django.urls import reverse
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.forms import ValidationError

from .models import *


class PropertyValuesFormField(forms.Field):
    """
    A form field for `custom_values_<type>`.

    It displayes fields for each property that is created for the specific Model and type.
    """
    def __init__(
            self, *,
            model: Type[models.Model],
            type: str,
            custom_properties: List[CustomProperty],
            label: str,
            help_text: str,
    ):
        super().__init__(
            required=False,
            label=label,
            help_text=help_text,
        )
        self.property_type = type
        if not custom_properties:
            self.widget = forms.HiddenInput()
            self.custom_properties_map = {}
        else:
            self.widget = PropertyValuesWidget(
                model=model,
                type=type,
                custom_properties=custom_properties,
            )
            self.custom_properties_map: Dict[int, CustomProperty] = {
                prop.pk: prop
                for prop in custom_properties
            }

    def validate(self, value):
        super().validate(value)
        if isinstance(value, dict):
            for pk, value in value.items():
                if prop := self.custom_properties_map.get(pk):
                    if choices := prop.get_choices():
                        if value and value not in choices:
                            raise ValidationError(
                                _("Property '{}' expects a choice of {}").format(
                                    prop.name,
                                    ", ".join(f"'{c}'" for c in choices)
                                )
                            )

    def prepare_value(self, value):
        # print("PREPARE_VALUE", self.label, value)
        return value

    def to_python(self, value) -> dict:
        #print("TO_PYTHON", value)
        if value in (None, "", [], "[]"):
            return {}
        if isinstance(value, dict):
            if self.property_type == "bool":
                value = {key: bool(v) for key, v in value.items()}
        return value


class PropertyValuesWidget(Input):
    template_name = "config_app/property_values_widget.html"

    def __init__(
            self,
            model: Type[models.Model],
            type: str,
            custom_properties: List[CustomProperty],
    ):
        super().__init__()
        self.model = model
        self.value_type = type
        self.custom_properties = custom_properties

    def format_value(self, value):
        """Just pass it through unchanged to the template get_context"""
        return value

    def value_from_datadict(self, data, files, name):
        values = {}
        for prop in self.custom_properties:
            key = f"custom-property-{prop.pk}"
            if key in data:
                values[prop.pk] = data[key]
        return values

    def get_context(self, name, value, attrs):
        ctx = super().get_context(name, value, attrs)
        values = ctx["widget"]["value"]
        #print("WIDGET VALUE", type(values), repr(values))
        ctx["properties"] = []

        for property in self.custom_properties:
            value = None
            if values:
                if isinstance(values, dict):
                    for pk, v in values.items():
                        if pk == property.pk:
                            value = v
                            break
                elif isinstance(values, (tuple, list)):
                    for propval in values:
                        if propval.property == property:
                            value = propval.value
                            break
            autocomplete_kwargs = {
                "class": "autocomplete-modelfield",
                "data-ac-json-url": reverse("ajax:model_json"),
                "data-ac-id": f"custom_property_{property.pk}",
            }
            if choices := property.get_choices():
                widget = forms.widgets.Select(choices=[("", "")] + [(c, c) for c in choices])
            elif property.type == "bool":
                widget = forms.widgets.CheckboxInput()
            elif property.type == "text":
                widget = forms.widgets.TextInput(autocomplete_kwargs)
            elif property.type == "text_long":
                widget = forms.widgets.Textarea(autocomplete_kwargs)
            else:
                raise NotImplementedError(f"CustomProperty.type '{self.value_type}'")

            ctx["properties"].append({
                "property": property,
                "widget": widget.render(
                    name=f"custom-property-{property.pk}",
                    value=value,
                ),
                "id": f"custom-property-{property.pk}",
            })
        return ctx


class CustomPropertyTabularInline(admin.TabularInline):
    """
    TODO: This is currently not working.
        The `custom_property_<pk>` id names for form fields are not prefixed with the inline row id.
        Need to find out how that goes at some point...
    """
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        fieldsets = custom_properties_patch_fieldsets(self.model, fieldsets)
        return fieldsets

    def get_formset(
        self, request, obj = ..., **kwargs
    ):
        fs = super().get_formset(request, obj, **kwargs)
        return fs


def custom_properties_patch_fieldsets(
        model: Union[models.Model, Type[models.Model]],
        fieldsets: Union[List, Tuple],
) -> Tuple:
    """
    Function to automatically add fields for `custom_values_<type>`
    if present on the model and if at least one CustomProperty for the model exists.

    The fields will be added at the end of the supplied fieldsets object.
    If they exist earlier (because of automatic field generation) they are removed there.

    :param model: django Model class or instance
    :param fieldsets: the object returned by `super().get_fieldsets(request, obj)`
    :return: patched fieldsets instance
    """
    # automatically add `custom_values_<type>` fields
    if props := [
        f"custom_values_{type}"
        for type in CUSTOM_PROPERTY_MODEL_TYPES
        if hasattr(model, f"custom_values_{type}")
    ]:
        # remove them from autogenerated fieldsets
        for entry in fieldsets:
            if len(entry) >= 2 and isinstance(entry[1], dict):
                if fields := entry[1].get("fields"):
                    entry[1]["fields"] = [f for f in fields if not str(f).startswith("custom_values_")]

        if CustomProperty.objects.filter(model=model._meta.label).exists():
            # and append them at the end
            fieldsets = list(fieldsets) + [
                (_('custom properties'), {
                    'classes': 'collapse',
                    'fields': props,
                }),
            ]

    return tuple(fieldsets)
