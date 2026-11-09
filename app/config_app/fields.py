import json
import warnings
from typing import Optional, Literal, Type, List

from django import forms
from django.forms.widgets import Input
from django.db import models, transaction, ProgrammingError
from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.contrib.auth import get_user_model

from .models import *
from .models.customprops import CUSTOM_PROPERTY_TYPE_CHOICES
from .forms import PropertyValuesFormField

User = get_user_model()

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
            to=CustomProperty.get_model_label(self.property_value_model_class),
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
            return [
                m for m in CustomProperty.get_properties_for_model(self.model)
                if m.type.startswith(self.property_type)
            ]
        # in case column does not exist before migration
        except ProgrammingError:
            return []

    def save_form_data(self, instance, data):
        with transaction.atomic():
            rel_manager = getattr(instance, f"custom_values_{self.property_type}", None)
            if not rel_manager:
                warnings.warn(f"save_form_data({instance}) without custom_values_{self.property_type} field")
                return
            existing_values = {
                v.property: v for v in rel_manager.all()
            }
            new_value_set = []
            changed = False
            for prop in self.get_custom_properties():
                value = data.get(prop.pk) or data.get(str(prop.pk))
                existing_value = existing_values.get(prop)

                if not value:
                    if existing_value:
                        existing_value.delete()
                        changed = True
                else:
                    if prop.type == "user":
                        try:
                            value = User.objects.get(username=value)
                        except User.DoesNotExist:
                            raise ValueError(f"User '{value}' does not exist")

                    if existing_value:
                        if value != existing_value.value:
                            existing_value.value = value
                            existing_value.save()
                        new_value_set.append(existing_value)
                    else:
                        new_value_set.append(self.property_value_model_class.objects.create(
                            property=prop,
                            value=value,
                        ))
                        changed = True

            if changed:
                rel_manager.set(new_value_set)


class CustomPropertyValuesBoolField(CustomPropertyValuesBaseField):
    property_value_model_class = PropertyValueBool
    property_type = "bool"
    verbose_name = _("bool values")


class CustomPropertyValuesTextField(CustomPropertyValuesBaseField):
    property_value_model_class = PropertyValueText
    property_type = "text"
    verbose_name = _("text values")


class CustomPropertyValuesUserField(CustomPropertyValuesBaseField):
    property_value_model_class = PropertyValueUser
    property_type = "user"
    verbose_name = _("user values")
