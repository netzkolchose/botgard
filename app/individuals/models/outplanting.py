from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.db.models.signals import post_save, pre_delete, post_init, m2m_changed
from django.utils.safestring import mark_safe
from django.dispatch import receiver

from .individual import Individual
from config_tables.admin import configurable, Configurable


class Outplanting(models.Model, Configurable):
    class Meta:
        verbose_name = _("Outplanting")
        verbose_name_plural = _("Outplantings")

    department = models.ForeignKey('individuals.Department', verbose_name=_("department"),
                                   null=True, on_delete=models.SET_DEFAULT, default=None)
    seeded_date = models.DateField(verbose_name=_("sowing date"), blank=True, null=True)
    date = models.DateField(verbose_name=_("bed out date"), blank=True, null=True)
    plant_died = models.DateField(verbose_name=_("plant died on"), blank=True, null=True)

    individual = models.ForeignKey(Individual, verbose_name=_("individual"), on_delete=models.CASCADE)

    def __str__(self):
        if self.department is None:
            if self.date is None:
                return 'xx %s' % (self.territory.code)
            else:
                return '%d-%d-%d %s illegal data set' % (
                self.date.year, self.date.month, self.date.day, self.territory.code)
        else:
            if self.date is None:
                return 'xx %s' % (self.department.code)
            else:
                return '%d-%d-%d %s' % (self.date.year, self.date.month, self.date.day, self.department.code)

    def is_alive(self, strong=False):
        """Runtime (non-DB) check for 'aliveness'"""
        if not strong:
            return self.plant_died is None
        return self.plant_died is None and not (self.seeded_date is None or self.date is None)

    @configurable
    def department_decorator(self):
        return "%s" % self.department
    department_decorator.short_description = _("department")
    department_decorator.admin_order_field = "department__code"

    @configurable
    def territory_decorator(self):
        return "%s" % self.department.territory
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


def _recalc_outplanting_fields(outplanting, exclude_outplanting=None):
    """
    Recalculate statistics for all Territories and Departments
    use `exclude_outplanting` to exclude an Outplanting instance from being counted
    """
    if outplanting.department:
        outplanting.department.calc_outplanting_fields(exclude_outplanting=exclude_outplanting)
        if outplanting.department.territory:
            outplanting.department.territory.calc_outplanting_fields(exclude_outplanting=exclude_outplanting)
    if outplanting.individual:
        outplanting.individual.calc_outplantings()


@receiver(post_save, sender=Outplanting)
def on_outplanting_save(sender, instance, **kwargs):
    #print("OUTPLANTING POSTSAVE %s %s %s" % (sender, instance, kwargs))
    _recalc_outplanting_fields(instance)


@receiver(pre_delete, sender=Outplanting)
def on_outplanting_delete(sender, instance, **kwargs):
    #print("DELETE %s %s %s" % (sender, instance, kwargs))
    _recalc_outplanting_fields(instance, exclude_outplanting=instance)

