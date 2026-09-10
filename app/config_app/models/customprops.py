from typing import Type, Union, List

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter
from django.contrib.auth import get_user_model

User = get_user_model()

CUSTOM_PROPERTY_MODEL_TYPES = ("bool", "text", "user")

CUSTOM_PROPERTY_TYPE_CHOICES = (
    ("bool", _("Boolean")),
    ("text", _("Text")),
    ("text_long", _("Text (long)")),
    ("user", _("User")),
)

CUSTOM_PROPERTY_MODEL_CHOICES = (
    ("botman.BGCIGarden", _("BGCI garden")),
    ("botman.BotanicGarden", _("botanic garden")),
    ("individuals.Territory", _("territory")),
    ("individuals.Department", _("department")),
    ("species.Family", _("genus")),
    ("species.Species", _("species")),
    ("entrybook.Entry", _("Seed/individual entry")),
    ("individuals.Individual", _("individual")),
    ("herbaria.Herbarium", _("Herbarium")),
    ("herbaria.HerbariumSpecimen", _("Specimen")),
    ("literature.Literature", _("literature")),
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
    )
    required = models.BooleanField(
        verbose_name=_("mandatory"),
        default=False,
    )
    order = models.IntegerField(
        verbose_name=_("order"),
        help_text=_("Order of field when viewing or editing."),
        default=0,
    )
    choices = models.TextField(
        verbose_name=_("choices"),
        help_text=_("For text properties, limits the selection to these items, one per line"),
        blank=True,
    )

    def __str__(self):
        name = self.model
        for (key, n) in CUSTOM_PROPERTY_MODEL_CHOICES:
            if key == self.model:
                name = n
                break
        return f"{name}/{self.name}"

    @classmethod
    def get_properties_for_model(self, model: Union[models.Model, Type[models.Model]]) -> List["CustomProperty"]:
        return list(CustomProperty.objects.filter(
            model=model._meta.label,
        ).order_by("order", "name"))

    def get_value_for_model(self, model: models.Model) -> Union[None, "PropertyValueBool", "PropertyValueText", "PropertyValueUser"]:
        type = self.type.split("_")[0]
        if rel_manager := getattr(model, f"custom_values_{type}"):
            return rel_manager.filter(property=self).first()

    def get_python_value_for_model(self, model: models.Model) -> Union[None, bool, str, User]:
        type = self.type.split("_")[0]
        if rel_manager := getattr(model, f"custom_values_{type}"):
            prop_value = rel_manager.filter(property=self).first()
            if prop_value:
                return prop_value.value
            if self.type == "bool":
                return False
            return None

    def get_decorator_value_for_model(self, model: models.Model):
        if v := self.get_value_for_model(model):
            return v.value_decorator()

    def get_choices(self) -> List[str]:
        if self.type in ("text", "text_long"):
            return list(filter(bool, (
                s.strip() for s in self.choices.splitlines()
            )))
        else:
            return []

    def create_list_filter(self) -> Type[SimpleListFilter]:
        prop = self
        class PropertyFilter(SimpleListFilter):
            parameter_name = f"custom_property_{prop.pk}"
            title = "-invisible-"  # gets display:none from extra-css
            def has_output(self):
                return True  # need to have output, otherwise django won't use the filter
            def lookups(self, request, model_admin):
                return []
            def queryset(self, request, queryset):
                if self.value() not in ("", None):
                    if prop.type == "bool":
                        if str(self.value()) == "1":
                            return queryset.filter(
                                custom_values_bool__property__pk=prop.pk,
                                custom_values_bool__value=True,
                            )
                    elif prop.type.startswith("text"):
                        return queryset.filter(
                            custom_values_text__property__pk=prop.pk,
                            custom_values_text__value__icontains=self.value(),
                        )
                    elif prop.type == "user":
                        # changelist user filter is a choice-box. so don't do icontains-comparison
                        return queryset.filter(
                            custom_values_user__property__pk=prop.pk,
                            custom_values_user__value__username=self.value(),
                        )
                    else:
                        raise NotImplementedError(prop.type)
                return queryset

        return PropertyFilter

    def change_link_decorator(self):
        return mark_safe('<a href="%d/" class="changelink">%s</a>' % (self.pk, _('show')))
    change_link_decorator.short_description = _('show')
    change_link_decorator.exclude_csv = True


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
        return f"{self.property.name}: {'✔' if self.value else '❌'}"

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

    # TODO: showing the full value could be disturbing in the admin views
    #   however, PropertyValue<Type> instances are not shown in changelist or changeform
    #   Right now, this is the workaround to show the values in read-only changeforms
    def __str__(self):
        return f"{self.property.name}: {self.value}"

    def value_decorator(self):
        return self.value


class PropertyValueUser(models.Model):
    class Meta:
        verbose_name = _("user value")
        verbose_name_plural = _("user values")

    _id_field = "pk"

    property = models.ForeignKey(
        verbose_name=_("custom property"),
        to=CustomProperty,
        on_delete=models.CASCADE,
        related_name="values_user",
    )
    value = models.ForeignKey(
        verbose_name=_("value"),
        to=User,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"{self.property.name}: {self.value}"

    def value_decorator(self):
        return self.value

    def save(self, *args, **kwargs):

        if isinstance(self.value, str):
            try:
                self.value = User.objects.get(username=self.value)
            except User.DoesNotExist:
                raise ValueError(f"User '{self.value}' does not exist")

        return super().save(*args, **kwargs)
