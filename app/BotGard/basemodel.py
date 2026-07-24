from typing import Optional, Type

from django.db import models


def BotGardBaseModel(
        configureable: bool = True,
        custom_properties_unique_name: Optional[str] = None,
) -> Type[models.Model]:
    """
    Return a base model class to derive your models from.

    Common base classes can be added here for easier handling.

    :param configureable: bool
        Add the config_tables.Configurable model mixin

    :param custom_properties_unique_name: optional str,
        If specified, the model supports custom properties.
        The string is some unique model-name in the Many2Many.related_name field, e.g.
        the model will have Many2Many fields like:

            custom_values_<type> = CustomPropertyValues<Type>Field(
                related_name="<custom_properties_unique_name>_values_<type>"
            )

        See config_app/baseclass.py

    :return: the requested django Model base class
    """
    from config_app.basemodel import CustomPropertiesBaseModel
    from config_tables.admin import Configurable

    klass = models.Model

    if custom_properties_unique_name:
        klass = CustomPropertiesBaseModel(related_name_model=custom_properties_unique_name)

    if configureable:

        class Model(Configurable, klass):
            class Meta:
                abstract = True

        klass = Model

    return klass
