from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.contrib.auth import get_user_model

from config_tables.admin import Configurable, configurable
from ajax.autocomplete import AutoCompleteForm
from tools.countries import ISO_COUNTRY_CHOICES
from BotGard import BotGardBaseModel


class BGCIGarden(BotGardBaseModel(custom_properties_unique_name="bgcigarden")):
    class Meta:
        verbose_name = _('BGCI garden')
        verbose_name_plural = _('BGCI gardens')

    _id_field = "bgci_id"

    bgci_id = models.IntegerField(verbose_name=_('BGCI id'), unique=True, blank=False, db_index=True)
    ipen_code = models.CharField(verbose_name=_('IPEN part'), max_length=7, null=True, blank=True, db_index=True)
    name = models.CharField(verbose_name=_('name'), max_length=128, db_index=True)
    type = models.CharField(verbose_name=_('type'), max_length=128)

    website = models.URLField(verbose_name=_('website'), max_length=1024, blank=True, null=True)
    phone = models.CharField(verbose_name=_('phone'), max_length=80, blank=True, null=True)
    email = models.EmailField(verbose_name=_('email'), blank=True, null=True)

    country = models.CharField(verbose_name=_('country'), max_length=2, choices=ISO_COUNTRY_CHOICES, null=True, blank=True)
    state_or_province = models.CharField(verbose_name=_('city'), max_length=64, null=True, blank=True)
    city = models.CharField(verbose_name=_('city'), max_length=64, null=True, blank=True)
    postal_code = models.CharField(verbose_name=_('postal code'), max_length=64, null=True, blank=True)
    address = models.TextField(verbose_name=_('address'), max_length=256, null=True, blank=True)

    bgci_data = models.JSONField(verbose_name=_("BGCI data"))

    def __str__(self):
        return f"{self.bgci_id}/{self.name}"

    @configurable
    def bgci_link_decorator(self):
        url = f"https://gardensearch.bgci.org/garden/{self.bgci_id}"
        return mark_safe('<a href="%s" target="_blank">%s</a>' % (url, _("website")))
    bgci_link_decorator.admin_order_field = 'website'
    bgci_link_decorator.short_description = _('BGCI website')
    bgci_link_decorator.as_csv = lambda s: s[s.index('<a href')+9:s.index('"', s.index('<a href')+9)] if "<a href" in s else s

    @configurable
    def email_link_decorator(self):
        if self.email:
            return mark_safe('<a href="mailto:%s">%s</a>' % (self.email, self.email[0:75]))
        else:
            return "-"
    email_link_decorator.admin_order_field = 'email'
    email_link_decorator.short_description = _('email')
    email_link_decorator.as_csv = lambda s: s[s.index('<a href')+16:s.index('"', s.index('<a href')+16)] if "<a href" in s else s


class BGCIGardenForm(AutoCompleteForm(BGCIGarden)):
    pass
