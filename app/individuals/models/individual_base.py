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

from picklefield.fields import PickledObjectField

#from botman.models import BotanicGarden
from seedcatalog.models import SeedCatalog
from tools.countries import ISO_COUNTRY_CHOICES
from tools.global_request import get_current_request
from ajax.autocomplete import AutoCompleteForm

from configuration.accession_extensions import ACCESSION_EXTENSION_CHOICES
from config_tables.admin import configurable, Configurable
#from geolocation.models import undefined_geolocation, undefined_osmlocation
from individuals.numbers import get_new_accession_number, get_new_order_number


IPEN_TRANSFER_RESTRICTIONS = (
    ('1', _('1 (transfer restricted)')),
    ('0', _('0 (transfer unrestriced)')),
)

CAME_IN_AS_CHOICES = (
    ('PF', _('Plant')),
    ('SA', _('Seed')),
    ('ST', _('Scion')),
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


class IndividualBase(models.Model):
    """
    Base class for
        - individuals.models.Individual
        - entrybook.models.Entry

    ForeignKey fields are added by `Individual`,
    while `Entry` uses CharFields for them.
    """

    class Meta:
        abstract = True

    accession_number = models.IntegerField(
        verbose_name=_("accession #"), blank=False, null=True, db_index=True,
        default=get_new_accession_number, unique=True
    )

    accession_extension = models.CharField(
        max_length=2, verbose_name=_("code of origin"),
        choices=ACCESSION_EXTENSION_CHOICES, blank=True, null=True
    )

    id_name_generated = models.CharField(
        max_length=100, verbose_name=_("name"),
        default="", editable=False
    )

    species_checked_by = models.CharField(
        max_length=100, verbose_name=_("plant categorized by"), blank=True
    )

    came_as_species = models.CharField(
        max_length=100, verbose_name=_("received as species"), blank=True
    )

    ipen_country = models.CharField(max_length=3, choices=ISO_COUNTRY_CHOICES, verbose_name="IPEN", db_index=True)
    ipen_transfer_restricted = models.CharField(max_length=1, choices=IPEN_TRANSFER_RESTRICTIONS, verbose_name="-")
    ipen_accession_number = models.CharField(max_length=50, verbose_name="-")

    source_date = models.DateField(verbose_name=_("date of receipt"), blank=True, null=True)
    came_in_as = models.CharField(
        max_length=2, choices=CAME_IN_AS_CHOICES, verbose_name=_("received as"), blank=True,
        db_index=True
    )

    found_country = models.CharField(
        max_length=3, choices=ISO_COUNTRY_CHOICES, verbose_name=_("collecting country"),
        blank=False, db_index=True
    )
    found_text = models.TextField(max_length=10000, verbose_name=_("collecting place description"), blank=True)
    collector_name = models.CharField(max_length=100, verbose_name=_("collector's name"), blank=True, null=False)
    collector_number = models.CharField(max_length=100, verbose_name=_("collection number"), blank=True)
    collector_date = models.DateField(verbose_name=_("collection date"), blank=True, null=True)

    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name=_("gender"), blank=True)
    comment = models.TextField(max_length=10000, verbose_name=_("comment"), blank=True)

    # helper field for searching and sorting for ipen
    ipen_generated = models.CharField(
        max_length=200, editable=False, null=True,
        verbose_name="IPEN"
    )

    seed_available = models.BooleanField(verbose_name=_("seed available"))
    order_number = models.IntegerField(verbose_name=_("order number"), unique=True, default=get_new_order_number)

    seed_collector_date = models.DateField(verbose_name=_("seed's collection date"), blank=True, null=True)
    seed_in_stock = models.BooleanField(verbose_name=_("seed in stock"))

    sowing_number = models.CharField(verbose_name=_("sowing number"), max_length=100, blank=True)

    # geo_location = models.ForeignKey("geolocation.GeoLocation", verbose_name=_("location (geonames)"),
    #                                  default=undefined_geolocation,
    #                                  on_delete=models.SET_DEFAULT)

    # osm_location = models.ForeignKey("geolocation.OsmLocation", verbose_name=_("location (osm)"),
    #                                  default=undefined_osmlocation,
    #                                  on_delete=models.SET_DEFAULT)

    def country_decorator(self):
        """Only needed by geolocation template"""
        cc = self.found_country
        for i in ISO_COUNTRY_CHOICES:
            if i[0] == cc:
                return i[1]
        return cc.upper()

    def found_text_lines(self):
        return self.found_text.split("\n")

    def came_in_as_text(self):
        for key, text in CAME_IN_AS_CHOICES:
            if self.came_in_as == key:
                return text
        return _('unknown')
