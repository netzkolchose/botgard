from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete, post_delete, post_init

from config_tables.admin import Configurable, configurable
from ajax.autocomplete import AutoCompleteForm
from tools.urls import full_url

import config_app

# TODO: replace get_new_number, link methods still needed?, save still needed?


config_app.register_key(
    "site_branding",
    _("Botanic Garden"),
    _("This name will appear at the top of all pages")
)


def get_new_number():
    '''
        get an available number for a new garden
    '''
    latest_garden = BotanicGarden.objects.all().order_by('-number')
    if not latest_garden.exists():
        new_number = 1
    else:
        new_number = latest_garden[0].number + 1
    return new_number


class BotanicGarden(Configurable, models.Model):
    class Meta:
        verbose_name = _('botanic garden')
        verbose_name_plural = _('botanic gardens')
        ordering = ('number',)
        # TODO: actually should have this:
        # unique_together = ("number", "code", "name")

    _id_field = "full_name_generated"

    name = models.CharField(verbose_name=_('name'), max_length=50, unique=True, db_index=True)
    code = models.CharField(verbose_name=_('IPEN part'), max_length=6, blank=True, null=True, db_index=True)
    number = models.IntegerField(verbose_name=_('garden number'), unique=True, blank=False, default=get_new_number)
    address = models.TextField(verbose_name=_('address'), max_length=255, blank=True, null=True)
    phone = models.CharField(verbose_name=_('phone'), max_length=80, blank=True, null=True)
    website = models.URLField(verbose_name=_('website'), blank=True, null=True)
    email = models.EmailField(verbose_name=_('email'), blank=True, null=True)

    full_name_generated = models.CharField(verbose_name=_('full name'), max_length=150, blank=True)
    num_orders_generated = models.IntegerField(verbose_name=_('number of orders'), default=0)
    catalog_date_generated = models.DateField(verbose_name=_('latest catalog date'), null=True)

    def __str__(self):
        return self.get_full_name()
    __str__.admin_order_field = 'number'
    __str__.short_description = _('botanic garden')
    __str__.searchable_field = 'full_name_generated'

    def get_full_name(self):
        return '%s (%s)' % (self.number, '/'.join([self.code if self.code else "-", self.name]))

    def address_lines(self):
        if self.address:
            return [
                l.strip(" ,")
                for l in self.address.splitlines()
            ]
        else:
            return []
    address_lines.template_doc = _(
        "Each line in the address is available separately, e.g. {{obj.botanicgarden.address_lines.0}}, {{obj.botanicgarden.address_lines.1}}, aso. "
    )

    @configurable
    def website_link_decorator(self):
        if self.website:
            return mark_safe('<a href="%s" target="_blank">%s</a>' % (full_url(self.website), self.website[0:40]))
        else:
            return "-"
    website_link_decorator.admin_order_field = 'website'
    website_link_decorator.short_description = _('website')
    website_link_decorator.as_csv = lambda s: s[s.index('<a href')+9:s.index('"', s.index('<a href')+9)] if "<a href" in s else s

    @configurable
    def email_link_decorator(self):
        if self.email:
            return mark_safe('<a href="mailto:%s">%s</a>' % (self.email, self.email[0:75]))
        else:
            return "-"
    email_link_decorator.admin_order_field = 'email'
    email_link_decorator.short_description = _('email')
    email_link_decorator.as_csv = lambda s: s[s.index('<a href')+16:s.index('"', s.index('<a href')+16)] if "<a href" in s else s

    @configurable
    def label_link_decorator(self):
        from labels import label_link_decorator
        return mark_safe(label_link_decorator("garden", self.pk, self.name))
        #return '<a href="%s" target="_blank">%s</a>' % (
        #    reverse('botman:label_shipping', args=(self.pk,)), _('label'))
    label_link_decorator.short_description = _('label')
    label_link_decorator.exclude_csv = True

    @configurable
    def change_link_decorator(self):
        return mark_safe('<a href="%d/" class="changelink">%s</a>' % (self.pk, _('show')))
    change_link_decorator.short_description = _('show')
    change_link_decorator.exclude_csv = True

    @configurable
    def delete_link_decorator(self):
        return mark_safe('<a href="%d/delete/" class="deletelink">%s</a>' % (self.pk, _('delete')))
    delete_link_decorator.short_description = _('delete')
    delete_link_decorator.exclude_csv = True

    def save(self, *args, **kawrgs):
        # fix django-admin bug and save NULL instead of an empty string
        self.code = self.code.upper() if self.code else None
        self.full_name_generated = self.get_full_name()
        self.num_orders_generated = 0
        self.catalog_date_generated = None
        if self.pk is not None:
            self.num_orders_generated = self.outgoing_orders.filter(processed=False).count()
            if self.catalogs.exists():
                self.catalog_date_generated = self.catalogs.order_by("-date_uploaded")[0].date_uploaded
        super(BotanicGarden, self).save(*args, **kawrgs)


class BotanicGardenForm(AutoCompleteForm(BotanicGarden)):
    pass
