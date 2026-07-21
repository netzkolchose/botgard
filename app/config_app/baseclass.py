from typing import Type

from django.db import models

from .models import *
from .fields import *


def CustomPropertiesBaseModel(related_name_model: str) -> Type[models.Model]:
    """
    Create a base model class to derive from that supports custom properties.

    :param related_name_model: str,
        The string is some unique model-name in the Many2Many.related_name field, e.g.
        the model will have Many2Many fields like:

            custom_values_<type> = CustomPropertyValues<Type>Field(
                related_name="<related_model_name>_values_<type>"
            )

    :return: a new django Model class
    """
    class _CustomPropertiesModel(models.Model):
        class Meta:
            abstract = True

        custom_values_bool = CustomPropertyValuesBoolField(related_name=f"{related_name_model}_values_bool")
        custom_values_text = CustomPropertyValuesTextField(related_name=f"{related_name_model}_values_text")

        def __getattr__(self, item):
            if not (isinstance(item, str) and item.startswith("custom_property_")):
                return super().__getattribute__(item)

            pk = item[16:]
            try:
                prop = (
                    self.custom_values_bool.filter(property__pk=pk).first()
                    or self.custom_values_text.filter(property__pk=pk).first()
                )
                return prop.value
            except:
                raise AttributeError(f"CustomProperty missing: {item}")


    return _CustomPropertiesModel
