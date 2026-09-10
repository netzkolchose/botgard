from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy
from django.utils.safestring import mark_safe
from django.urls import reverse
from django import forms
from django.contrib import admin

from BotGard import BotGardBaseModel
from config_tables.admin import Configurable, configurable, CustomSelectHeaderFilter
from ajax.autocomplete import AutoCompleteForm


class Project(BotGardBaseModel(unique_name="project", custom_properties=True)):
    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')
        ordering = ("full_name_generated", )

    _id_field = "full_name_generated"

    abbreviation = models.CharField(
        verbose_name=_("abbreviation"),
        max_length=32,
        blank=True,
    )

    title = models.CharField(
        verbose_name=_("title"),
        max_length=128,
    )

    date_start = models.DateField(
        verbose_name=_("start date"),
        null=True, blank=True,
    )

    date_end = models.DateField(
        verbose_name=_("end date"),
        null=True, blank=True,
    )

    manager = models.TextField(
        verbose_name=_("manager(s)"),
        blank=True,
    )

    partner = models.TextField(
        verbose_name=_("partner(s)"),
        blank=True,
    )

    funding = models.TextField(
        verbose_name=_("funding agency"),
        blank=True,
    )

    comment = models.TextField(
        verbose_name=_("comment"),
        blank=True,
    )

    full_name_generated = models.CharField(
        verbose_name=_("full name"),
        max_length=256,
        editable=False,
        unique=True,
    )

    def __str__(self):
        return self.full_name_generated

    @configurable
    def change_link_decorator(self):
        return mark_safe('<a href="%d/" class="changelink">%s</a>' % (self.pk, _('show')))
    change_link_decorator.short_description = _('show')
    change_link_decorator.exclude_csv = True

    def save(self, *args, **kwargs):
        if self.abbreviation:
            name = f"({self.abbreviation}) {self.title}"
        else:
            name = self.title

        self.full_name_generated = name
        super().save(*args, **kwargs)


class ProjectForm(AutoCompleteForm(Project)):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if field := self.fields.get("title"):
            field.widget.attrs["style"] = "width: 25rem;"

