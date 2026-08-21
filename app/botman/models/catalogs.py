from typing import Type

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
from BotGard import BotGardBaseModel


def ExternalCatalogBase(unique_name: str):
    class ExternalCatalogBase(BotGardBaseModel(
        unique_name=unique_name,
        creation_fields=False,
    )):
        class Meta:
            abstract = True

        garden = models.ForeignKey(
            verbose_name=_("Botanic garden"),
            to="BotanicGarden",
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

    return ExternalCatalogBase


class ExternalCatalog(ExternalCatalogBase(unique_name="externalcatalog")):
    class Meta:
        verbose_name = _('external catalog')
        verbose_name_plural = _('external catalogs')
        ordering = ('date_uploaded',)


class ExternalCatalogArchive(ExternalCatalogBase(unique_name="externalcatalogarchive")):
    class Meta:
        verbose_name = _('external catalog (archived)')
        verbose_name_plural = _('external catalogs (archived)')
        ordering = ('date_uploaded',)

    garden = models.ForeignKey(
        verbose_name=_("Botanic garden"),
        to="BotanicGarden",
        on_delete=models.CASCADE,
        related_name="catalogs_archived",
    )


class ExternalCatalogForm(AutoCompleteForm(ExternalCatalog)):
    pass


class ExternalCatalogArchiveForm(AutoCompleteForm(ExternalCatalogArchive)):
    pass


class OutgoingOrder(BotGardBaseModel(unique_name="outgoingorder", creation_fields=False)):
    class Meta:
        verbose_name = _('outgoing order')
        verbose_name_plural = _('outgoing orders')
        ordering = ('date_created',)

    garden = models.ForeignKey(
        verbose_name=_("Botanic garden"),
        to="BotanicGarden",
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
        try:
            garden, user = self.garden, self.user
        except:
            garden, user = None, None

        if garden and user:
            return str(_("outgoing order/%(garden)s/%(user)s %(date)s") % {
                "garden": garden,
                "user": user,
                "date": self.date_created,
            })
        return str(_("outgoing order"))

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
        instance.garden.save(_no_creation_fields=True)


@receiver(post_delete, sender=OutgoingOrder)
def on_outgoing_order_delete(sender, instance, **kwargs):
    if instance.garden:
        instance.garden.save(_no_creation_fields=True)


@receiver(post_save, sender=ExternalCatalog)
def on_external_catalog_save(sender, instance, **kwargs):
    if instance.garden:
        instance.garden.save(_no_creation_fields=True)


@receiver(post_delete, sender=ExternalCatalog)
def on_external_catalog_delete(sender, instance, **kwargs):
    if instance.garden:
        instance.garden.save(_no_creation_fields=True)
