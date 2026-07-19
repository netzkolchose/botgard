import json
from typing import Optional, Literal, Type, List

from django import forms
from django.forms.widgets import Input
from django.db import models

from .models import *


class PropertyValuesFormField(forms.Field):

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
        else:
            self.widget = PropertyValuesWidget(
                model=model,
                type=type,
                custom_properties=custom_properties,
            )

    def prepare_value(self, value):
        # print("VALUE", value)
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
        # print("WIDGET VALUE", type(values), values)
        ctx["properties"] = []

        for property in self.custom_properties:
            value = None
            if values:
                for v in values:
                    if v.property == property:
                        value = v.value
                        break
            if property.type == "bool":
                widget = forms.widgets.CheckboxInput()
            elif property.type == "text":
                if choices := property.get_choices():
                    widget = forms.widgets.Select(choices=[("", "")] + [(c, c) for c in choices])
                else:
                    widget = forms.widgets.TextInput()
            elif property.type == "text_long":
                widget = forms.widgets.Textarea()
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
