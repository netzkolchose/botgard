import pprint
from typing import Type

from django.db import models

from .models import *
from .fields import *


registered_custom_property_classes = []


def CustomPropertiesBaseModel(related_name_model: str) -> Type[models.Model]:
    """
    Create a base model class to derive from that supports custom properties.

    Note that ModelAdmin functionality to make them work in changelists
    is placed in `config_tables.ConfigurableTable`.
    So customprop models need to use this specific ModelAdmin.

    :param related_name_model: str,
        The string is some unique model-name in the `Many2Many.related_name` field, e.g.
        the model will have Many2Many fields like:

            custom_values_<type> = CustomPropertyValues<Type>Field(
                related_name="<related_model_name>_values_<type>"
            )

    :return: a new django Model class
    """
    class _CustomPropertiesModel(models.Model):
        class Meta:
            abstract = True

        _has_custom_properties = True

        custom_values_bool = CustomPropertyValuesBoolField(related_name=f"{related_name_model}_values_bool")
        custom_values_text = CustomPropertyValuesTextField(related_name=f"{related_name_model}_values_text")
        custom_values_user = CustomPropertyValuesUserField(related_name=f"{related_name_model}_values_user")

        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)

            if "Base" in cls.__name__ or cls.__name__ == "Model":
                return

            registered_custom_property_classes.append(cls)

        def __getattr__(self, item):
            if not (isinstance(item, str) and item.startswith("custom_property_")):
                return super().__getattribute__(item)

            pk = item[16:]
            try:
                prop = (
                    self.custom_values_bool.filter(property__pk=pk).first()
                    or self.custom_values_text.filter(property__pk=pk).first()
                    or self.custom_values_user.filter(property__pk=pk).first()
                )
                return prop.value
            except:
                raise AttributeError(f"CustomProperty missing: {item}")


    return _CustomPropertiesModel


def check_custom_property_classes():
    """
    Called on BotGard app ready, to warn if the
    CustomProperty.model choices don't fit the registered models
    """
    expected_class_names = {}
    for c in registered_custom_property_classes:
        key = f"{c.__module__.split('.')[0]}.{c.__name__}"
        if key != "individuals.Seed":  # this is only a proxy of Individual
            expected_class_names[key] = c

    class_names = set(i[0] for i in CUSTOM_PROPERTY_MODEL_CHOICES)

    if class_names != set(expected_class_names):
        msg = f"config_app CUSTOM_PROPERTY_MODEL_CHOICES does not match all registered model class"
        missing = set(expected_class_names) - class_names
        if missing:
            msg += f"\nMissing:\n{pprint.pformat(sorted(missing))}"
        too_much = class_names - set(expected_class_names)
        if too_much:
            msg += f"\nToo much:\n{pprint.pformat(sorted(too_much))}"

        msg += "\n\nit should look like this:\n\n"
        msg += "CUSTOM_PROPERTY_MODEL_CHOICES = (\n"
        for name, cls in expected_class_names.items():
            tr_name = name.split(".")[-1]
            proxy = cls._meta.verbose_name
            if proxy:
                if args := getattr(proxy, "_args", None):
                    proxy = args[0]
                tr_name = str(proxy)

            msg += f"""    ("{name}", _("{tr_name}")),\n"""
        msg += ")\n"

        warnings.warn(msg)
