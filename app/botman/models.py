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
    if not latest_garden.exists():  # if no other garden exists
        new_number = 1
    else:
        new_number = latest_garden[0].number + 1
    return new_number


class BotanicGarden(Configurable, models.Model):
    class Meta:
        verbose_name = _('botanic garden')
        verbose_name_plural = _('botanic gardens')
        ordering = ('number',)

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
        "Each line in the address is available separately, e.g. {{address_lines.0}}, {{address_lines.1}}, aso. "
    )

    @configurable
    def website_link_decorator(self):
        if self.website:
            return mark_safe('<a href="%s" target="_blank">%s</a>' % (self.website, self.website[0:40]))
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
        self.num_orders_generated = self.outgoing_orders.filter(processed=False).count()
        self.catalog_date_generated = None
        if self.catalogs.exists():
            self.catalog_date_generated = self.catalogs.order_by("-date_uploaded")[0].date_uploaded
        super(BotanicGarden, self).save(*args, **kawrgs)


class BotanicGardenForm(AutoCompleteForm(BotanicGarden)):
    pass


class ExternalCatalog(Configurable, models.Model):
    class Meta:
        verbose_name = _('external catalog')
        verbose_name_plural = _('external catalogs')
        ordering = ('date_uploaded',)

    garden = models.ForeignKey(
        verbose_name=_("Botanic garden"),
        to=BotanicGarden,
        on_delete=models.CASCADE,
        related_name="catalogs",
    )

    date_uploaded = models.DateField(
        verbose_name=_("Date incoming"),
        default=timezone.now,
    )

    date_outgoing = models.DateField(
        verbose_name=_("Date outgoing"),
        null=True, blank=True,
    )

    file = models.FileField(
        verbose_name=_("Catalog file"),
        upload_to="garden-catalogs/"
    )

    def __str__(self):
        if self.garden:
            return str(_("garden catalog/%(garden)s/%(date)s") % {
                "garden": self.garden,
                "date": self.date_uploaded
            })
        return str(_("garden catalog/%(date)s") % {
            "date": self.date_uploaded
        })

    @configurable
    def delete_link_decorator(self):
        url = reverse("admin:botman_externalcatalog_delete", args=(self.pk,))
        return mark_safe('<a href="%s" class="deletelink">%s</a>' % (url, _('delete')))
    delete_link_decorator.short_description = _('delete')
    delete_link_decorator.exclude_csv = True

    @configurable
    def num_orders_decorator(self):
        if not self.garden:
            return 0

        # only show for newest catalog
        qset = self.garden.catalogs.all().order_by("-date_uploaded").values_list("pk", flat=True)
        if qset.exists() and self.pk != qset[0]:
            return 0

        return self.garden.num_orders_generated
    num_orders_decorator.admin_order_field = "garden__num_orders_generated"
    num_orders_decorator.short_description = _('number of orders')

    @configurable
    def garden_link_decorator(self):
        if self.garden:
            url = reverse("admin:botman_botanicgarden_change", args=(self.garden.pk,))
            return mark_safe('<a href="%s" class="changelink">%s</a>' % (url, self.garden))
        return "-"
    garden_link_decorator.admin_order_field = "garden__full_name_generated"
    garden_link_decorator.short_description = _('Botanic garden')


class ExternalCatalogForm(AutoCompleteForm(ExternalCatalog)):
    pass


class OutgoingOrder(Configurable, models.Model):
    class Meta:
        verbose_name = _('outgoing order')
        verbose_name_plural = _('outgoing orders')
        ordering = ('date_created',)

    garden = models.ForeignKey(
        verbose_name=_("Botanic garden"),
        to=BotanicGarden,
        on_delete=models.CASCADE,
        related_name="outgoing_orders",
    )

    date_created = models.DateField(
        verbose_name=_("Creation date"),
        auto_now=True,
    )

    user = models.ForeignKey(
        verbose_name=_("Ordered by user"),
        to=get_user_model(),
        on_delete=models.CASCADE,
        related_name="outgoing_orders",
    )

    order_text = models.TextField(
        verbose_name=_("Order text"),
    )

    processed = models.BooleanField(
        verbose_name=_("Processed"),
        default=False
    )

    def __str__(self):
        if self.garden and self.user:
            return _("outgoing order/%(garden)s/%(user)s") % {
                "garden": self.garden,
                "user": self.user,
            }
        return _("outgoing order")

    @configurable
    def garden_link_decorator(self):
        if self.garden:
            url = reverse("admin:botman_botanicgarden_change", args=(self.garden.pk,))
            return mark_safe('<a href="%s" class="changelink">%s</a>' % (url, self.garden))
        return "-"
    garden_link_decorator.admin_order_field = "garden__full_name_generated"
    garden_link_decorator.short_description = _('Botanic garden')
    garden_link_decorator.exclude_csv = True

    @configurable
    def garden_email_decorator(self):
        if self.garden and self.garden.email:
            return mark_safe('<a href="mailto:%s">%s</a>' % (self.garden.email, self.garden.email[0:75]))
        else:
            return "-"
    garden_email_decorator.admin_order_field = 'garden__email'
    garden_email_decorator.short_description = _('garden email')
    garden_email_decorator.as_csv = lambda s: s[s.index('<a href')+16:s.index('"', s.index('<a href')+16)] if "<a href" in s else s

    @configurable
    def user_email_decorator(self):
        if self.user and self.user.email:
            return mark_safe('<a href="mailto:%s">%s</a>' % (self.user.email, self.user.email[0:75]))
        else:
            return "-"
    user_email_decorator.admin_order_field = 'user__email'
    user_email_decorator.short_description = _('user email')
    user_email_decorator.as_csv = lambda s: s[s.index('<a href')+16:s.index('"', s.index('<a href')+16)] if "<a href" in s else s


    @configurable
    def catalog_date(self):
        if self.garden:
            return self.garden.catalog_date_generated
    catalog_date.admin_order_field = 'garden__catalog_date_generated'
    catalog_date.short_description = _('latest catalog date')


class OutgoingOrderForm(AutoCompleteForm(OutgoingOrder)):
    pass


# ----- recalc: BotanicGarden.num_orders_generated and catalog_date -----

@receiver(post_save, sender=OutgoingOrder)
def on_outgoing_order_save(sender, instance, **kwargs):
    if instance.garden:
        instance.garden.save()


@receiver(post_delete, sender=OutgoingOrder)
def on_outgoing_order_delete(sender, instance, **kwargs):
    if instance.garden:
        instance.garden.save()


@receiver(post_save, sender=ExternalCatalog)
def on_external_catalog_save(sender, instance, **kwargs):
    if instance.garden:
        instance.garden.save()


@receiver(post_delete, sender=ExternalCatalog)
def on_external_catalog_delete(sender, instance, **kwargs):
    if instance.garden:
        instance.garden.save()
