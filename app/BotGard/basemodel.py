from typing import Optional, Type

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


def BotGardBaseModel(
        unique_name: str,
        creation_fields: bool = True,
        configurable: bool = True,
        custom_properties: bool = False,
) -> Type[models.Model]:
    """
    Return a base model class to derive your models from.

    Common base classes can be added here for easier handling.

    :param unique_name: str,
        The string is some unique model-name in foreign key fields for the `related_name` property

    :param creation_fields: bool
        Add `created_by`, `created_date`, `modified_by`, `modified_date` fields

    :param configurable: bool
        Add the config_tables.Configurable model mixin

    :param custom_properties: bool,
        If True, the model supports custom properties.
        The model will have Many2Many fields like:

            custom_values_<type> = CustomPropertyValues<Type>Field(
                related_name="<unique_name>_values_<type>"
            )

        See config_app/baseclass.py

    :return: the requested django Model base class
    """
    from config_app.basemodel import CustomPropertiesBaseModel
    from config_tables.admin import Configurable
    from tools.global_request import get_current_user

    klass = models.Model

    if custom_properties:
        klass = CustomPropertiesBaseModel(related_name_model=unique_name)

    if creation_fields:

        class Model(klass):
            class Meta:
                abstract = True

            created_by = models.ForeignKey(
                verbose_name=_("created by"),
                to=get_user_model(),
                on_delete=models.CASCADE,
                null=True, blank=True,
                related_name=f"{unique_name}_created_users",
            )
            created_date = models.DateField(
                verbose_name=_("created at"),
                null=True, blank=True,
            )
            modified_by = models.ForeignKey(
                verbose_name=_("modified by"),
                to=get_user_model(),
                on_delete=models.CASCADE,
                null=True, blank=True,
                related_name=f"{unique_name}_modified_users",
            )
            modified_date = models.DateField(
                verbose_name=_("modified at"),
                null=True, blank=True,
            )

            def save(self, *args, **kwargs):
                user = get_current_user()
                if not self.pk:
                    self.created_date = timezone.now().date()
                    self.created_by = user
                else:
                    self.modified_date = timezone.now().date()
                    self.modified_by = user
                return super().save(*args, **kwargs)

        klass = Model

    if configurable:

        class Model(Configurable, klass):
            class Meta:
                abstract = True

        klass = Model

    return klass
