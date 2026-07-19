import json
import warnings
from typing import Optional, Literal, Type, List

from django import forms
from django.forms.widgets import Input
from django.db import models, transaction, ProgrammingError
from django.utils.translation import gettext_lazy as _
from django.apps import apps

from .models import *
from .models.customprops import CUSTOM_PROPERTY_TYPE_CHOICES
from .forms import PropertyValuesFormField


class CustomPropertyValuesBaseField(models.ManyToManyField):

    # needs to be set to `PropertyValueBool` etc in subclasses
    property_value_model_class = None
    # needs to be set to `bool`, `text` etc in subclasses
    property_type = None
    verbose_name = None

    def __init__(
            self,
            related_name: str,
            **kwargs,
    ):
        super().__init__(
            verbose_name=self.verbose_name,
            to=self.property_value_model_class._meta.label,
            related_name=related_name,
        )

    def formfield(
        self,
        **kwargs,
    ):
        return PropertyValuesFormField(
            model=self.model,
            custom_properties=self.get_custom_properties(),
            type=self.property_type,
            label=self.verbose_name,
            help_text=self.help_text,
        )

    def get_custom_properties(self) -> List[CustomProperty]:
        # avoid reading database during start-up
        if not apps.ready:
            return []

        try:
            return list(CustomProperty.objects.filter(
                model=self.model._meta.label,
                type=self.property_type,
            ).order_by("order", "name"))
        # in case column does not exist before migration
        except ProgrammingError:
            return []

    def save_form_data(self, instance, data):
        # print("SAVE_FORM_DATA", repr(instance), data)
        with transaction.atomic():
            rel_manager = getattr(instance, f"custom_values_{self.property_type}", None)
            if not rel_manager:
                warnings.warn(f"save_form_data({instance}) without custom_values_{self.property_type} field")
                return
            existing_values = {
                v.property: v for v in rel_manager.all()
            }
            new_value_set = []
            for prop in self.get_custom_properties():
                value = data.get(prop.pk) or data.get(str(prop.pk))
                existing_value = existing_values.get(prop)

                if not value:
                    if existing_value:
                        existing_value.delete()
                else:
                    if existing_value:
                        existing_value.value = value
                        existing_value.save()
                        new_value_set.append(existing_value)
                    else:
                        new_value_set.append(self.property_value_model_class.objects.create(
                            property=prop,
                            value=value,
                        ))

            rel_manager.set(new_value_set)


class CustomPropertyValuesBoolField(CustomPropertyValuesBaseField):
    property_value_model_class = PropertyValueBool
    property_type = "bool"
    verbose_name = _("bool values")


class CustomPropertyValuesTextField(CustomPropertyValuesBaseField):
    property_value_model_class = PropertyValueText
    property_type = "text"
    verbose_name = _("text values")
