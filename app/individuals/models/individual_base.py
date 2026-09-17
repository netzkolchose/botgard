from typing import Type

from django.db import models, OperationalError
from django import forms
from django.forms import widgets
from django.forms.utils import ErrorList
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy as __
from django.urls import reverse
from django.templatetags.static import static
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
#from django.db.models.signals import post_save
#from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model

from picklefield.fields import PickledObjectField

#from botman.models import BotanicGarden
from seedcatalog.models import SeedCatalog
from tools.countries import ISO_COUNTRY_CHOICES, get_iso_country_name
from tools.global_request import get_current_request
from ajax.autocomplete import AutoCompleteForm

from configuration.accession_extensions import ACCESSION_EXTENSION_CHOICES
from config_tables.admin import configurable, Configurable
from individuals.numbers import get_new_accession_number, get_new_order_number
from BotGard import BotGardBaseModel


IPEN_TRANSFER_RESTRICTIONS = (
    ('1', _('1 (transfer restricted)')),
    ('0', _('0 (transfer unrestriced)')),
)

CAME_IN_AS_CHOICES = (
    ('PF', _('Plant')),
    ('PT', _('Plant part')),
    ('SA', _('Seed')),
    ('SÄ', _('Seedling')),
    ('ST', _('Scion')),
    ('SP', _('Spores')),
    ('UN', _('unknown')),
)

GENDER_CHOICES = (
    ('M', _('male')),
    ('W', _('female')),
    ('Z', _('hermaphrodite')),
    ('X', _('unknown'))
)

NOTE_CHOICES = (
    ('W', _('wild seed')),
    ('KW', _('cultivated wild plant')),
    ('KG', _('cultivated plant')),
)


def IndividualBase(unique_name: str) -> Type[models.Model]:
    """
    Base class for
        - individuals.models.Individual
        - entrybook.models.Entry

    ForeignKey fields are added by `Individual`,
    while `Entry` uses CharFields for them.
    """
    class IndividualBase(BotGardBaseModel(unique_name=unique_name, custom_properties=True)):
        class Meta:
            abstract = True

        accession_number = models.CharField(
            verbose_name=_("accession #"), blank=False, null=True, db_index=True,
            max_length=30,
            default=get_new_accession_number, unique=True,
            db_collation="natural_sort" if settings.IS_POSTGRES else None,
        )

        accession_extension = models.CharField(
            max_length=2, verbose_name=_("code of origin"),
            choices=ACCESSION_EXTENSION_CHOICES, blank=True, null=True
        )

        id_name_generated = models.CharField(
            max_length=100, verbose_name=_("name"),
            default="", editable=False,
            db_collation="natural_sort" if settings.IS_POSTGRES else None,
        )

        species_checked_by = models.CharField(
            max_length=100, verbose_name=_("plant categorized by"), blank=True
        )
        species_checked_date = models.DateField(
            verbose_name=_("categorized at"), null=True, blank=True,
        )

        came_as_species = models.CharField(
            max_length=100, verbose_name=_("received as species"), blank=True
        )

        species_comment = models.CharField(
            verbose_name=_("comment (determination)"),
            max_length=1024,
            blank=True,
        )

        literature = models.ForeignKey(
            verbose_name=_("literature"),
            to="literature.Literature",
            on_delete=models.SET_NULL,
            null=True, blank=True,
            related_name="individuals",
        )

        ipen_country = models.CharField(max_length=3, choices=ISO_COUNTRY_CHOICES, verbose_name="IPEN", db_index=True)
        ipen_transfer_restricted = models.CharField(max_length=1, choices=IPEN_TRANSFER_RESTRICTIONS, verbose_name="-")
        ipen_accession_number = models.CharField(max_length=50, verbose_name="-")

        source_date = models.DateField(verbose_name=_("date of receipt"), blank=True, null=True)
        came_in_as = models.CharField(
            max_length=2, choices=CAME_IN_AS_CHOICES, verbose_name=_("received as"), blank=True,
            db_index=True
        )
        external_order_number = models.CharField(
            verbose_name=_("External order number"),
            max_length=64,
            null=True, blank=True,
        )

        found_country = models.CharField(
            max_length=3, choices=ISO_COUNTRY_CHOICES, verbose_name=_("collecting country"),
            blank=False, db_index=True
        )
        found_text = models.TextField(max_length=10000, verbose_name=_("collecting place description"), blank=True)
        collector_name = models.CharField(max_length=100, verbose_name=_("collector's name"), blank=True, null=False)
        collector_number = models.CharField(
            max_length=100, verbose_name=_("collection number"), blank=True,
            db_collation="natural_sort" if settings.IS_POSTGRES else None,
        )
        collector_date = models.DateField(verbose_name=_("collection date"), blank=True, null=True)

        gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name=_("gender"), blank=True)
        comment = models.TextField(max_length=10000, verbose_name=_("comment"), blank=True)

        # helper field for searching and sorting for ipen
        ipen_generated = models.CharField(
            max_length=200, editable=False, null=True,
            verbose_name="IPEN"
        )

        seed_available = models.BooleanField(verbose_name=_("seed available"))
        order_number = models.CharField(
            verbose_name=_("order number"), max_length=20, unique=True, default=get_new_order_number,
            db_collation="natural_sort" if settings.IS_POSTGRES else None,
        )

        seed_collector_date = models.DateField(verbose_name=_("seed's collection date"), blank=True, null=True)
        seed_in_stock = models.BooleanField(verbose_name=_("seed in stock"))

        sowing_number = models.CharField(
            verbose_name=_("sowing number"), max_length=100, blank=True,
            db_collation="natural_sort" if settings.IS_POSTGRES else None,
        )

        projects = models.ManyToManyField(
            verbose_name=_("project assignment"),
            to="meta.Project",
            related_name="individuals",
            blank=True,
        )

        import_reference = models.CharField(
            verbose_name=_("import reference"),
            max_length=64, null=True, blank=True,
            help_text=_("a reference number in an external data source")
        )
        status = models.CharField(
            verbose_name=_("status"),
            max_length=128, null=True, blank=True,
        )

        def found_country_name(self) -> str:
            """Full name of `found_country` code"""
            return get_iso_country_name(self.found_country)
        found_country_name.template_doc = _("collecting country name")

        def found_text_lines(self):
            return self.found_text.split("\n")

        def came_in_as_text(self):
            for key, text in CAME_IN_AS_CHOICES:
                if self.came_in_as == key:
                    return text
            return _('unknown')

    return IndividualBase
