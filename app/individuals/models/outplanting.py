from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.db.models.signals import post_save, pre_delete, post_init, m2m_changed
from django.utils.safestring import mark_safe
from django.dispatch import receiver
import django.contrib.gis.db.models as gis_models
from django.contrib.gis.geos import Point
import django.contrib.gis.forms as gis_forms
from django import forms

from geo.util import geo_coord_to_html
from .individual import Individual
from .territory import Department
from config_tables.admin import configurable, Configurable
from ajax.autocomplete import AutoCompleteForm
from geo.widgets import BotGardOpenLayersWidget
from BotGard import BotGardBaseModel


class Outplanting(BotGardBaseModel(unique_name="outplanting")):
    class Meta:
        verbose_name = _("Outplanting")
        verbose_name_plural = _("Outplantings")

    individual = models.ForeignKey(Individual, verbose_name=_("individual"), on_delete=models.CASCADE)
    department = models.ForeignKey('individuals.Department', verbose_name=_("department"),
                                   null=True, on_delete=models.SET_DEFAULT, default=None)
    location = gis_models.PointField(
        verbose_name=_("location"),
        srid=4326,
        db_index=True,
        geography=True,
        null=True, blank=True,
    )
    seeded_date = models.DateField(verbose_name=_("sowing date"), blank=True, null=True)
    date = models.DateField(verbose_name=_("bed out date"), blank=True, null=True)
    plant_died = models.DateField(verbose_name=_("plant died on"), blank=True, null=True)
    comment = models.TextField(
        verbose_name=_("comment"),
        null=True, blank=True,
    )

    def __str__(self):
        if self.department is None:
            name = _("Outplanting") + f" {self.pk}"
        else:
            name = self.department.full_code

        if self.date is None:
            return 'xx %s' % name
        else:
            return '%d-%d-%d %s' % (self.date.year, self.date.month, self.date.day, name)

    def is_alive(self, strong=False):
        """Runtime (non-DB) check for 'aliveness'"""
        if not strong:
            return self.plant_died is None
        return self.plant_died is None and not (self.seeded_date is None or self.date is None)

    @configurable
    def change_link_decorator(self):
        return _("show")
    change_link_decorator.short_description = _("show")
    change_link_decorator.exclude_csv = True

    @configurable
    def department_decorator(self):
        return "%s" % self.department if self.department else "-"
    department_decorator.short_description = _("department")
    department_decorator.admin_order_field = "department__code"

    @configurable
    def territory_decorator(self):
        return "%s" % self.department.territory if self.department else "-"
    territory_decorator.short_description = _("territory")
    territory_decorator.admin_order_field = "department__territory__code"

    @configurable
    def individual_link_decorator(self):
        url = reverse("admin:individuals_individual_change", args=(self.individual.pk,))
        return mark_safe('<a href="%s">%s</a>' % (url, self.individual.ipen_generated))
    individual_link_decorator.short_description = _("individual")
    individual_link_decorator.admin_order_field = "individual__ipen_generated"

    @configurable
    def family_single(self):
        return self.individual.species.family.family
    family_single.short_description = _('family')
    family_single.admin_order_field = "individual__species__family__family"

    @configurable
    def genus_single(self):
        return self.individual.species.family.genus
    genus_single.short_description = _('genus')
    genus_single.admin_order_field = "individual__species__family__genus"

    @configurable
    def location_decorator(self):
        if not self.location:
            return ""
        return mark_safe(geo_coord_to_html(self.location))
    location_decorator.short_description = _("location")
    location_decorator.admin_order_field = "location"

    @configurable
    def map_decorator(self):
        from geo.columns import map_outplantings_column_decorator

        outplantings = []
        if self.is_alive() and self.location:
            outplantings = [{"location": self.location}]
        return map_outplantings_column_decorator(
            id=self.pk,
            outplantings=outplantings,
        )
    map_decorator.short_description = _("Map")
    map_decorator.exclude_csv = True


class OutplantingForm(AutoCompleteForm(Outplanting)):
    exclude_autocomplete = ["department"]
    location = gis_forms.PointField(
        srid=Outplanting.location.field.srid,
        widget=BotGardOpenLayersWidget(
            with_garden_map=True,
            with_input_fields=True,
            red_dots=True, map_size=[200, 200],
        ),
        required=False,
    )


def _recalc_outplanting_fields(outplanting, exclude_outplanting=None):
    """
    Recalculate statistics for all Territories and Departments
    use `exclude_outplanting` to exclude an Outplanting instance from being counted
    """
    from individuals.models import Department, Territory, Individual
    # catches DoesNotExists errors for `manage.py loaddata`
    try:
        if outplanting.department:
            outplanting.department.calc_outplanting_fields(exclude_outplanting=exclude_outplanting)
            try:
                if outplanting.department.territory:
                    outplanting.department.territory.calc_outplanting_fields(exclude_outplanting=exclude_outplanting)
            except Territory.DoesNotExist:
                pass
    except Department.DoesNotExist:
        pass
    try:
        if outplanting.individual:
            outplanting.individual.calc_outplantings()
    except Individual.DoesNotExist:
        pass


_RECEIVE_OUTPLANTING_SIGNALS = True

@receiver(post_save, sender=Outplanting)
def on_outplanting_save(sender, instance, **kwargs):
    if _RECEIVE_OUTPLANTING_SIGNALS:
        #print("OUTPLANTING POSTSAVE %s %s %s" % (sender, instance, kwargs))
        _recalc_outplanting_fields(instance)


@receiver(pre_delete, sender=Outplanting)
def on_outplanting_delete(sender, instance, **kwargs):
    if _RECEIVE_OUTPLANTING_SIGNALS:
        # print("DELETE %s %s %s" % (sender, instance, kwargs))
        _recalc_outplanting_fields(instance, exclude_outplanting=instance)

