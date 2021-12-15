from django.db import models, OperationalError
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ungettext_lazy as __
from django.utils.safestring import mark_safe
from django.urls import reverse
from django import forms
from picklefield.fields import PickledObjectField

from ajax.autocomplete import AutoCompleteForm
from config_tables.admin import configurable, Configurable
import config_app



def _to_percent_deco(x, n):
    return "%s%%" % ((round(float(x) / n * 100, 2)) if n > 0 else 0.)


class CalcOutplantingsMixin(models.Model):
    """
    Abstract Model Mixin for Outplanting statistics
    """
    class Meta:
        abstract = True

    num_outplantings = models.IntegerField(verbose_name=_("# outplantings"), default=0, editable=False)
    num_individuals = models.IntegerField(verbose_name=_("# individuals"), default=0, editable=False)
    num_species = models.IntegerField(verbose_name=_("# species"), default=0, editable=False)
    num_genera = models.IntegerField(verbose_name=_("# genera"), default=0, editable=False)

    num_outplantings_alive = models.IntegerField(verbose_name=_("# outplantings alive"), default=0, editable=False)
    num_individuals_alive = models.IntegerField(verbose_name=_("# individuals alive"), default=0, editable=False)
    num_species_alive = models.IntegerField(verbose_name=_("# species alive"), default=0, editable=False)
    num_genera_alive = models.IntegerField(verbose_name=_("# genera alive"), default=0, editable=False)

    def _get_outplanting_filter(self):
        """Get Django DB query for Outplanting objects.
        To be implemented by derived class"""
        raise NotImplementedError

    def get_outplantings(self, exclude_outplanting=None):
        """Returns QuerySet of Outplantings"""
        from .outplanting import Outplanting
        qset = Outplanting.objects.filter(**self._get_outplanting_filter())
        if exclude_outplanting is not None:
            qset = qset.exclude(pk=exclude_outplanting.pk)
        return qset

    def calc_outplanting_fields(self, do_save=True, exclude_outplanting=None):
        if not hasattr(self, 'num_outplantings'):
            return
        """Counts the number of outplantings for the Territory or Department"""
        locations = self.get_outplantings(exclude_outplanting)
        locations_alive = locations.filter(plant_died=None)

        self.num_outplantings = locations.count()
        self.num_individuals = locations.values_list("individual").distinct().count()
        self.num_species = locations.values_list("individual__species").distinct().count()
        if hasattr(self, "num_genera"):
            self.num_genera = locations.values_list("individual__species__family__genus").distinct().count()

        self.num_outplantings_alive = locations_alive.count()
        self.num_individuals_alive = locations_alive.values_list("individual").distinct().count()
        self.num_species_alive = locations_alive.values_list("individual__species").distinct().count()
        if hasattr(self, "num_genera"):
            self.num_genera_alive = locations_alive.values_list("individual__species__family__genus").distinct().count()
        if do_save:
            self.save()
    
    def num_outplantings_alive_percent(self):
        return _to_percent_deco(self.num_outplantings_alive, self.num_outplantings)

    def num_individuals_percent(self):
        return _to_percent_deco(self.num_individuals, self.num_outplantings)

    def num_individuals_alive_percent(self):
        return _to_percent_deco(self.num_individuals_alive, self.num_individuals)

    def num_species_percent(self):
        return _to_percent_deco(self.num_species, self.num_individuals)

    def num_species_alive_percent(self):
        return _to_percent_deco(self.num_species_alive, self.num_species)

    def num_genera_percent(self):
        return _to_percent_deco(self.num_genera, self.num_individuals)

    def num_genera_alive_percent(self):
        return _to_percent_deco(self.num_genera_alive, self.num_genera)


class Territory(CalcOutplantingsMixin, models.Model, Configurable):
    class Meta:
        verbose_name = _("territory")
        verbose_name_plural = _("territories")
        ordering = ['code']

    code = models.CharField(max_length=3, unique=True, verbose_name=_("territory code"))
    name = models.CharField(max_length=50, unique=True, verbose_name=_("territory name"))

    name_generated = models.CharField(max_length=70, verbose_name=_("display name"), default="", editable=False)

    _id_field = "name_generated"

    def __str__(self):
        return self.name_generated
    __str__.admin_order_field = 'name_generated'

    def _get_outplanting_filter(self):
        return dict(department__territory=self.pk)

    @configurable
    def change_link_decorator(self):
        url = reverse("admin:individuals_territory_change", args=(self.pk,))
        return mark_safe('<a href="%s" class="changelink">%s</a>' % (url, _("show")))
    change_link_decorator.short_description = _("show")
    change_link_decorator.exclude_csv = True

    @configurable
    def delete_link_decorator(self):
        url = reverse("admin:individuals_territory_delete", args=(self.pk,))
        return mark_safe('<a href="%s" class="deletelink">%s</a>' % (url, _("delete")))
    delete_link_decorator.short_description = _("delete")
    delete_link_decorator.exclude_csv = True

    @configurable
    def list_link_decorator(self):
        url = reverse("individuals:checklist_territory", args=(self.pk,))
        return mark_safe('<a href="%s">%s</a>' % (url, _("generate list")))
    list_link_decorator.short_description = _("List of individuals")
    list_link_decorator.exclude_csv = True

    def save(self, *args, **kwargs):
        # update name_generated
        if hasattr(self, "name_generated"):
            self.name_generated = "%s (%s)" % (self.code, self.name)

        has_changed = False
        if self.id:
            try:
                prev = Territory.objects.get(id=self.id)
                if prev.code != self.code:
                    has_changed = True
            except Territory.DoesNotExist:
                pass

        super(Territory, self).save(*args, **kwargs)

        # update Department.full_code
        if has_changed:
            for d in Department.objects.filter(territory=self):
                d.save()

    def num_departments(self):
        return Department.objects.filter(territory=self).count()


class TerritoryForm(AutoCompleteForm(Territory)):
    pass


def _department_full_code_validator(val):
    from django.forms import ValidationError
    if not isinstance(val, list):
        raise ValidationError(_('A list is expected.'))
    if len(val) < 1:
        raise ValidationError(_('The list must contain at least two values.'))
    if ('department' not in val):
        raise ValidationError(_('The list must contain "department".'))

config_app.register_key(
    "department_full_code",
    ["territory", "-", "department"],
    _("""Generation of a full code for a department. A list is expected.<br>
    Valid values for the list items are:
    <dl> 
    <dt>territory</dt><dd>for the territory code,</dd> 
    <dt>department</dt><dd>for the department code.</dd>
    </dl> 
    Any other string will be concatenated into the full code.<br> 
    Note that changes affect only newly created departments. To change existing departments run<br> 
    <b>./manage.py botgard_data_all</b>"""),
    _department_full_code_validator
)


class Department(CalcOutplantingsMixin, models.Model, Configurable):
    class Meta:
        verbose_name = _("department")
        verbose_name_plural = _("departments")
        ordering = ['code']

    territory = models.ForeignKey(
        Territory, on_delete=models.SET_DEFAULT, verbose_name=_("territory"), db_index=True,
        null=True, default=None,
    )
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=50, unique=True)

    full_code = models.CharField(max_length=30, default="", editable=False)

    def _get_outplanting_filter(self):
        return dict(department=self.pk)

    @configurable
    def __str__(self):
        return "%s (%s)" % (self.full_code, self.name)
    __str__.admin_order_field = 'code'

    @configurable
    def change_link_decorator(self):
        return mark_safe('<a href="%d/" class="changelink">%s</a>' % (self.pk, _("show")))
    change_link_decorator.short_description = _("show")
    change_link_decorator.exclude_csv = True

    @configurable
    def list_link_decorator(self):
        url = reverse("individuals:checklist_department", args=(self.pk,))
        return mark_safe('<a href="%s">%s</a>' % (url, _("generate list")))
    list_link_decorator.short_description = _("List of individuals")
    list_link_decorator.exclude_csv = True

    @configurable
    def delete_link_decorator(self):
        url = reverse("admin:individuals_department_delete", args=(self.pk,))
        return mark_safe('<a href="%s" class="deletelink">%s</a>' % (url, _("delete")))
    delete_link_decorator.short_description = _("delete")
    delete_link_decorator.exclude_csv = True

    def _get_individuals(self):
        """Returns all individuals that live in this Department"""
        locations = self.get_outplantings()
        indi_set = set()
        for i in locations:
            indi_set.add(i.individual)
        return indi_set

    def _get_full_code(self):
        """Helper function to generate the full code for a department.
        The value is stored in DB in full_code field."""
        values = config_app.get_value("department_full_code")
        ret = ""
        for v in values:
            if v == "territory":
                if self.territory:
                    ret += self.territory.code
            elif v == "department":
                ret += self.code
            else:
                ret += "%s" % v
        return ret

    def save(self, *args, **kwargs):
        # set full code
        self.full_code = self._get_full_code()

        prev_territory = None
        has_changed = False
        if self.id:
            try:
                prev = Department.objects.get(id=self.id)
                prev_territory = prev.territory
                if prev.full_code != self.full_code:
                    has_changed = True
            except Department.DoesNotExist:
                pass

        super(Department, self).save(*args, **kwargs)

        # when department moved to another territory
        if prev_territory is not None and prev_territory != self.territory:
            prev_territory.calc_outplanting_fields()
            self.territory.calc_outplanting_fields()

        # update Individual.living_outplantings
        if has_changed:
            for i in self._get_individuals():
                i.calc_outplantings()


class DepartmentForm(AutoCompleteForm(Department)):

    def clean(self):
        super(DepartmentForm, self).clean()

        # make sure territory/code combination is unique
        code = self.cleaned_data.get("code", "")
        terr = self.cleaned_data.get("territory", 0)
        qset = Department.objects.filter(code=code, territory=terr)
        if self.instance and self.instance.id:
            qset = qset.exclude(pk=self.instance.id)
        if qset.count() > 0:
            raise forms.ValidationError(
                _("A Department with code %(code)s in territory %(terr)s already exists") % {
                    "code": code, "terr": terr },
                code="duplicate"
            )
        return self.cleaned_data
