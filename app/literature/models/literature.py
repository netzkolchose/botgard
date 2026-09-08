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


class Literature(BotGardBaseModel(unique_name="literature", custom_properties=True)):
    class Meta:
        verbose_name = _('literature')
        verbose_name_plural = _('literature')
        ordering = ('title', 'year')
        unique_together = ('title', 'compilation', 'volume', 'print_run', 'year', 'page', 'location')

    _id_field = "full_name_generated"

    authors = models.CharField(
        verbose_name=_("author(s)"),
        max_length=128,
        blank=True,
    )

    title = models.CharField(
        verbose_name=_("title"),
        max_length=128,
        blank=True,
    )

    compilation = models.CharField(
        verbose_name=_("compilation/magazine"),
        max_length=128,
        blank=True,
    )

    volume = models.CharField(
        verbose_name=_("volume"),
        max_length=64,
        blank=True,
    )

    print_run = models.CharField(
        verbose_name=_("print run"),
        max_length=32,
        blank=True,
    )

    year = models.SmallIntegerField(
        verbose_name=_("year"),
        null=True, blank=True,
    )

    page = models.CharField(
        verbose_name=_("page(s)"),
        max_length=32,
        blank=True,
    )

    place = models.CharField(
        verbose_name=_("place"),
        max_length=64,
        blank=True,
    )

    publisher = models.CharField(
        verbose_name=_("publisher"),
        max_length=128,
        blank=True,
    )

    keywords = models.CharField(
        verbose_name=_("keywords"),
        max_length=256,
        blank=True,
    )

    location = models.CharField(
        verbose_name=_("location"),
        help_text=_("Where to find it"),
        max_length=128,
        blank=True,
    )

    signature = models.CharField(
        verbose_name=_("signature"),
        max_length=64,
        blank=True,
    )

    full_name_generated = models.CharField(
        verbose_name=_("full name"),
        max_length=4096,
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
        name = self.authors
        if name and not name.endswith("."):
            name += "."
        if self.year:
            if name:
                name = f"{name} {self.year}"
            else:
                name = self.year
        if name:
            name = f"{name}. "
        name = '{}"{}"'.format(name, self.title or _("untitled"))
        if self.compilation:
            name = f"{name} {self.compilation}"
        if self.page:
            name = f"{name}: {self.page}"
        if self.volume:
            name = "{}, {} {}".format(name, _("vol."), self.volume)
        if self.print_run:
            name = "{}, {} {}".format(name, _("pr."), self.print_run)

        # make sure `full_name_generated` is unique (according to Meta.unique_together)
        qset = self.__class__.objects.filter(full_name_generated=name)
        if self.pk:
            qset = qset.exclude(pk=self.pk)
        if qset.exists():
            name = f"{name} ({self.location})"

        self.full_name_generated = name
        super().save(*args, **kwargs)


class LiteratureForm(AutoCompleteForm(Literature)):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, field in self.fields.items():
            if isinstance(field, forms.CharField):
                field.widget.attrs["style"] = "width: 40rem;"

