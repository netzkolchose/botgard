from typing import Type

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe


CUSTOM_PROPERTY_TYPE_CHOICES = (
    ("bool", _("Boolean")),
    ("text", _("Text")),
)

CUSTOM_PROPERTY_MODEL_CHOICES = (
    ("species.Species", _("species")),
)


class CustomProperty(models.Model):
    class Meta:
        verbose_name = _("custom property")
        verbose_name_plural = _("custom properties")
        ordering = ("model", "name")
        unique_together = ("model", "name")

    date_created = models.DateTimeField(
        verbose_name=_("created at"),
        auto_now_add=True,
    )
    model = models.CharField(
        verbose_name=_("model"),
        choices=CUSTOM_PROPERTY_MODEL_CHOICES,
        max_length=64,
    )
    type = models.CharField(
        verbose_name=_("type"),
        choices=CUSTOM_PROPERTY_TYPE_CHOICES,
    )
    name = models.CharField(
        verbose_name=_("name"),
        unique=True,
    )
    order = models.IntegerField(
        verbose_name=_("order"),
        help_text=_("Order of value when viewing or editing."),
        default=0,
    )

    def __str__(self):
        name = self.model
        for (key, n) in CUSTOM_PROPERTY_MODEL_CHOICES:
            if key == self.model:
                name = n
                break
        return f"{name}.{self.name}"

    def get_value_for_model(self, model: models.Model):
        if rel_manager := getattr(model, f"custom_values_{self.type}"):
            v = rel_manager.filter(property=self).first()
            if v:
                return v.value

    def get_decorator_value_for_model(self, model: models.Model):
        if rel_manager := getattr(model, f"custom_values_{self.type}"):
            v = rel_manager.filter(property=self).first()
            if v:
                return v.value_decorator()


class PropertyValueBool(models.Model):
    class Meta:
        verbose_name = _("boolean value")
        verbose_name_plural = _("boolean values")

    _id_field = "pk"

    property = models.ForeignKey(
        verbose_name=_("custom property"),
        to=CustomProperty,
        on_delete=models.CASCADE,
        related_name="values_bool",
    )
    value = models.BooleanField(
        verbose_name=_("value"),
    )

    def __str__(self):
        return f"{self.property}"

    def value_decorator(self):
        return mark_safe('<span class="icon-%s"></span>' % (
            "yes" if self.value else "no",
        ))

class PropertyValueText(models.Model):
    class Meta:
        verbose_name = _("text value")
        verbose_name_plural = _("text values")

    _id_field = "pk"

    property = models.ForeignKey(
        verbose_name=_("custom property"),
        to=CustomProperty,
        on_delete=models.CASCADE,
        related_name="values_text",
    )
    value = models.CharField(
        verbose_name=_("value"),
        max_length=256,
    )

    def __str__(self):
        return f"{self.property}"

    def value_decorator(self):
        return self.value

