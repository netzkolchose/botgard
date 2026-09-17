import datetime

from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy as __
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.html import format_html, escape
from django.urls import reverse

from BotGard.basemodel import BotGardBaseModel
from config_tables.admin import configurable
from ajax.autocomplete import AutoCompleteForm
from individuals.numbers import get_new_dispatch_number


TRANSFER_TYPE_CHOICES = (
    ("plant", _("Plant")),
    ("leave", _("Leave")),
    ("branch", _("Branch")),
    ("seed", _("Seed")),
    ("scion", _("Scion")),
    ("gene_sample", _("Gene sample")),
    ("biomass", _("Biomass")),
)


class Dispatch(BotGardBaseModel(unique_name="dispatch", custom_properties=True)):

    class Meta:
        verbose_name = _("dispatch")
        verbose_name_plural = _("dispatches")
        ordering = ("date", "dispatch_number",)

    _id_field = "id_name_generated"

    dispatch_number = models.CharField(
        verbose_name=_("dispatch number"),
        max_length=32,
        unique=True,
        db_index=True,
        default=get_new_dispatch_number,
        db_collation="natural_sort" if settings.IS_POSTGRES else None,
    )

    date = models.DateField(
        verbose_name=_("event date"),
        db_index=True,
        default=datetime.date.today,
    )

    destination = models.ForeignKey(
        verbose_name=_("destination"),
        to="botman.BotanicGarden",
        on_delete=models.CASCADE,
        related_name="dispatches",
        db_index=True,
    )

    individual = models.ForeignKey(
        verbose_name=_("individual"),
        to="individuals.Individual",
        on_delete=models.CASCADE,
        related_name="dispatches",
        db_index=True,
    )

    transfer_type = models.CharField(
        verbose_name=_("transfer type"),
        max_length=32,
        choices=TRANSFER_TYPE_CHOICES,
        db_index=True,
    )

    amount = models.CharField(
        verbose_name=_("amount"),
        max_length=32,
        db_collation="natural_sort" if settings.IS_POSTGRES else None,
        db_index=True,
    )

    transfer_by = models.ForeignKey(
        verbose_name=_("transfer by"),
        to=get_user_model(),
        on_delete=models.CASCADE,
        related_name="dispatches",
        db_index=True,
    )

    comment = models.TextField(
        verbose_name=_("comment"),
        max_length=2048,
        blank=True,
    )

    projects = models.ManyToManyField(
        verbose_name=_("project assignment"),
        to="meta.Project",
        related_name="dispatches",
        blank=True,
        db_index=True,
    )

    id_name_generated = models.CharField(
        verbose_name=_("name"),
        max_length=256,
        unique=True,
        db_index=True,
        editable=False,
    )

    @configurable
    def __str__(self):
        return self.id_name_generated
    __str__.admin_order_field = 'id_name_generated'
    __str__.short_description = _('dispatch')

    @configurable
    def change_link_decorator(self):
        return _("show")
    change_link_decorator.short_description = _("show")
    change_link_decorator.exclude_csv = True

    @configurable
    def label_link_decorator(self):
        from labels import label_link_decorator
        return label_link_decorator(
            "garden", self.destination.pk, filename=self.individual.ipen_generated
        )
    label_link_decorator.short_description = _("create label")
    label_link_decorator.exclude_csv = True

    @configurable
    def individual_link_decorator(self):
        return mark_safe(format_html(
            """
            <a href="{}">{}</a>
            """,
            reverse("admin:individuals_individual_change", args=(self.individual.pk,)),
            self.individual,
        ))
    individual_link_decorator.short_description = _("individual")
    individual_link_decorator.admin_order_field = "individual__id_name_generated"

    def save(self, *args, **kwargs):
        self.id_name_generated = f"{self.dispatch_number} ({self.individual})"
        super().save(*args, **kwargs)


class DispatchForm(AutoCompleteForm(Dispatch)):
    exclude_autocomplete = ("projects", )

