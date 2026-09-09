import datetime
import json
from typing import List

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy as __
from django.contrib.admin.filters import FieldListFilter, AllValuesFieldListFilter
from django.template import Template, Context, Engine
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.html import mark_safe
from django.contrib.auth import get_user_model
from django.utils import timezone

from config_tables.admin import CustomSelectHeaderFilter
from geo.util import geo_coord_to_html
from species.models import Species
from tools.admin_extensions import minimal_admin_context
from tools.global_request import get_current_user
from .individual_base import *
from individuals.numbers import generate_individual_ipen
from individuals.widgets import SpeciesAuditWidget


User = get_user_model()


class Individual(IndividualBase(unique_name="individual")):

    class Meta:
        verbose_name = _("individual")
        verbose_name_plural = _("individuals")
        unique_together = ("ipen_country", "ipen_transfer_restricted", "ipen_accession_number", "ipen_garden_code")

    _id_field = "id_name_generated"

    user = models.ForeignKey(
        verbose_name=_("Created by"),
        to=get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        related_name="individuals",
    )

    ipen_garden_code = models.ForeignKey('botman.BotanicGarden', verbose_name="-", on_delete=models.CASCADE)
    species = models.ForeignKey(
        'species.Species', verbose_name=_("genus & Species"), blank=False,
        on_delete=models.CASCADE
    )
    source = models.ForeignKey(
        'botman.BotanicGarden', related_name="source_key", verbose_name=_("source"), blank=True,
        null=True, on_delete=models.CASCADE
    )

    # --- audit fields ---

    # format is list of
    # {
    #    "date": "YYYY-MM-DD"|None,
    #    "user": "username", "user_pk": int|None,
    #    "species": "full_name_generated", "species_pk": int,
    #    "literature": "full_name_generated"|None, "literature_pk": int|None,
    # }
    species_audit = models.JSONField(
        verbose_name=_("Determination audit"),
        null=True, blank=True,
    )

    # --- generated fields ---

    # list of PKs of Outplanting
    alive_outplantings_generated = PickledObjectField(
        verbose_name=_("alive_outplantings_generated"),
        default=None, blank=True, null=True
    )
    outplantings_generated = PickledObjectField(
        verbose_name=_("outplantings_generated"),
        default=None, blank=True, null=True
    )

    # department codes as text
    departments_generated = models.CharField(max_length=1000, verbose_name=_("departments"), blank=True)
    # territory codes as text
    territories_generated = models.CharField(max_length=1000, verbose_name=_("territories"), blank=True)
    # is any of the outplantings alive?
    is_alive_generated = models.BooleanField(verbose_name=_("is alive"), editable=False, default=False)
    has_specimen_generated = models.BooleanField(verbose_name=_("has specimen"), editable=False, default=False)

    @configurable
    def __str__(self):
        return self.id_name_generated
    __str__.admin_order_field = 'id_name_generated'
    __str__.short_description = _('Individual')

    def calc_outplantings(self, do_save=True):
        """
        Calculate and store the following fields:
        - outplantings_generated
        - alive_outplantings_generated
        - departments_generated
        - territories_generated
        - is_alive_generated
        """
        from .outplanting import Outplanting
        from .territory import Department
        locations = Outplanting.objects.filter(individual=self.pk)
        locations_alive = locations.filter(plant_died=None)

        self.outplantings_generated = [t[0] for t in locations.values_list("id")]
        self.alive_outplantings_generated = [t[0] for t in locations_alive.values_list("id")]
        try:
            self.departments_generated = " ".join(sorted(set(
                l.department.full_code for l in locations if l.department)))
            self.territories_generated = " ".join(
                "(%s)" % i
                for i in sorted(set(
                    l.department.territory.code
                    for l in locations
                    if l.department and l.department.territory
                ))
            )
        except Department.DoesNotExist:
            pass
        self.is_alive_generated = locations_alive.count() > 0
        if do_save:
            self.save(_no_creation_fields=True)

    def get_outplantings(self, alive_only=True) -> list:
        """Returns list of belonging Outplanting instances from database-cache"""
        from .outplanting import Outplanting
        ids = self.alive_outplantings_generated if alive_only else self.outplantings_generated
        if not ids:
            return []
        outpl = []
        for id in ids:
            try:
                outpl.append(Outplanting.objects.get(pk=id))
            except Outplanting.DoesNotExist:
                pass
        return outpl

    def get_outplanting_locations(self, alive_only=True) -> List[dict]:
        """Returns list of belonging Outplanting instances from database-cache"""
        from .outplanting import Outplanting
        qset = self.outplanting_set.all()
        qset = qset.exclude(location=None)
        if alive_only:
            qset = qset.filter(plant_died=None)
        return list(qset.values("pk", "location"))

    def _get_departments_html(self):
        links = []
        deps = {elem.department.full_code: elem.department
                for elem in self.get_outplantings(alive_only=False)
                if elem.department}
        #print(self.get_outplantings(alive_only=True))
        for code in sorted(deps):
            department = deps[code]
            url = reverse("admin:individuals_department_change", args=(department.pk,))
            links.append('<a href="%s" title="%s">%s</a> ' % (
                url, department.name, department.full_code.replace(" ", "&nbsp;")))
        return mark_safe("<br/>\n".join(links))

    def _get_territories_html(self):
        links = []
        deps = {elem.department.territory.code: elem.department.territory
                for elem in self.get_outplantings(alive_only=False)
                if elem.department and elem.department.territory}
        for code in sorted(deps):
            territory = deps[code]
            url = reverse("admin:individuals_territory_change", args=(territory.pk,))
            links.append('<a href="%s" title="%s">%s</a> ' % (
                url, territory.name, territory.code.replace(" ", "&nbsp;")))
        return mark_safe("<br/>\n".join(links))

    @configurable
    def change_link_decorator(self):
        return _("show")

    change_link_decorator.short_description = _("show")
    change_link_decorator.exclude_csv = True

    @configurable
    def delete_link_decorator(self):
        url = reverse("admin:individuals_individual_delete", args=(self.pk,))
        return mark_safe('<a href="%s" class="deletelink">%s</a>' % (url, _("delete")))

    delete_link_decorator.short_description = _("delete")
    delete_link_decorator.exclude_csv = True

    @configurable
    def etikett_link_decorator(self):
        from labels import label_link_decorator
        return label_link_decorator(
            label_class="individual",
            object_pk=self.pk,
            filename=self.ipen_generated,
            nomenclature_unchecked=not self.species.nomenclature_checked,
        )

    etikett_link_decorator.short_description = _("create label")
    etikett_link_decorator.exclude_csv = True

    @configurable
    def species_link_decorator(self):
        url = reverse("admin:species_species_change", args=(self.species.pk,))
        return mark_safe('<a href="%s">%s</a>' % (url, self.species))
    species_link_decorator.short_description = __("species", "species", 1)
    species_link_decorator.admin_order_field = "species"
    # redirection to field for filter-list
    # can also be a non-foreign field
    species_link_decorator.searchable_field = "species__full_name_generated"

    @configurable
    def family_single(self):
        return self.species.family.family
    family_single.short_description = _('family')
    family_single.admin_order_field = "species__family__family"

    @configurable
    def genus_single(self):
        return self.species.family.genus
    genus_single.short_description = _('genus')
    genus_single.admin_order_field = "species__family__genus"

    @configurable
    def endangering_decorator(self):
        return "%s" % self.species.protection_of_species

    endangering_decorator.short_description = _("endangering")
    endangering_decorator.admin_order_field = "species__protection_of_species"
    endangering_decorator.searchable_field = "species__protection_of_species"

    @configurable
    def departments_decorator(self):
        return self._get_departments_html()
    departments_decorator.short_description = _("departments")
    departments_decorator.admin_order_field = "departments_generated"

    @configurable
    def territories_decorator(self):
        return self._get_territories_html()
    territories_decorator.short_description = _("territories")
    territories_decorator.admin_order_field = "territories_generated"

    @configurable
    def nomenclature_checked_decorator(self):
        icon_url = static('admin/img/icon-%s.svg' %
                          {True: 'yes', False: 'no', None: 'unknown'}[self.species.nomenclature_checked])
        return mark_safe(format_html('<img src="{}" alt="{}" />', icon_url, self.species.nomenclature_checked))
    nomenclature_checked_decorator.short_description = _("nomenclature checked")
    nomenclature_checked_decorator.admin_order_field = "species__nomenclature_checked"

    @configurable
    def etikett_text_decorator(self):
        return self.species.area_of_distribution_etikettxt
    etikett_text_decorator.short_description = _("label text")
    etikett_text_decorator.admin_order_field = "species__area_of_distribution_etikettxt"

    @configurable
    def etikett_detail_decorator(self):
        return self.species.area_of_distribution_background
    etikett_detail_decorator.short_description = _("detailed")
    etikett_detail_decorator.admin_order_field = "species__area_of_distribution_background"

    @configurable
    def is_alive(self):
        return mark_safe('<span class="icon-%s"></span>' % (
            "yes" if self.is_alive_generated else "no",
        ))
    is_alive.short_description = _("is alive")
    is_alive.admin_order_field = "is_alive_generated"

    @configurable
    def image_decorator(self):
        from plantimages.models import PlantImage
        from easy_thumbnails.files import get_thumbnailer
        from easy_thumbnails.exceptions import InvalidImageFormatError

        qset = PlantImage.objects.filter(individual=self)
        if not qset.exists():
            return ""
        image = qset.order_by("pk")[0]
        url = "%s%s" % (settings.MEDIA_URL, image.image)
        try:
            thumb_url = get_thumbnailer(image.image)['preview'].url
        except InvalidImageFormatError:
            return ""
        alt = image.comment
        return mark_safe('<a href="%s" title="%s" target="_blank"><img src="%s" alt="%s"/></a>' % (url, alt, thumb_url, alt))
    image_decorator.short_description = _("image")
    image_decorator.exclude_csv = True

    def species_lines(self):
        """Special function to output a multiline string for use with labels"""
        spec_name = self.species.full_name(with_author=False)

        line1 = ''
        line2 = ''

        split_index = spec_name.find("subsp.")

        if split_index >= 0:
            line1 = spec_name[0:split_index]
            line2 = spec_name[split_index:]
            return line1, line2

        spec_name = spec_name.split()

        if len(spec_name) == 2:
            line1 = self.species.family.genus
            line2 = self.species.species
        else:
            for elem in spec_name:
                if len(line1) < 15:
                    line1 += u" %s" % elem
                else:
                    line2 += u" %s" % elem
            line1 = line1[1:]
            line2 = line2[1:]

        #if line2 == self.species.get_author_name():
        #    line2 = ""
        return line1, line2

    @configurable
    def locations_decorator(self):
        outplantings = self.get_outplanting_locations(alive_only=True)
        if not outplantings:
            return ""
        links = []
        for outpl in outplantings:
            links.append(geo_coord_to_html(outpl["location"]))
        return mark_safe(", ".join(links))
    locations_decorator.short_description = _("locations")

    @configurable
    def map_decorator(self):
        from geo.columns import map_outplantings_column_decorator

        outplantings = self.get_outplanting_locations(alive_only=True)
        return map_outplantings_column_decorator(
            id=self.pk,
            outplantings=outplantings,
        )
    map_decorator.short_description = _("Map")
    map_decorator.exclude_csv = True

    def save(self, *args, **kwargs):
        # -- update generated fields --
        self.ipen_generated = generate_individual_ipen(self)

        # -- update id_name_generated --
        self.id_name_generated = (
            "%s (%s)" % (self.accession_number, self.species.full_name(with_author=False))
        )[:100]

        # -- save Individual --
        super(Individual, self).save(*args, **kwargs)

    def add_species_audit(self, original_instance: "Individual"):
        """
        Add audit for species if it has changed.
        If nothing has changed, copy `species_audit` from `original_instance`.

        :param original_instance: instance of Individual before changes to self.species
        """
        if (
                original_instance.species == self.species
                and original_instance.species_checked_by == self.species_checked_by
                and original_instance.species_checked_date == self.species_checked_date
                and original_instance.literature == self.literature
        ):
            self.species_audit = original_instance.species_audit
            return

        audit = original_instance.species_audit
        if not audit:  # reconstruct first determination entry
            user = None
            user_pk = None
            if original_instance.species_checked_by:
                user = original_instance.species_checked_by
                if u := User.objects.filter(username=original_instance.species_checked_by).first():
                    user_pk = u.pk
            else:
                if u := original_instance.created_by:
                    user = u.username
                    user_pk = u.pk
            audit = [{
                "date": original_instance.species_checked_date or original_instance.created_date,
                "user": user,
                "user_pk": user_pk,
                "species": original_instance.species.full_name_generated,
                "species_pk": original_instance.species.pk,
                "literature": original_instance.literature.full_name_generated
                    if original_instance.literature else None,
                "literature_pk": original_instance.literature.pk
                    if original_instance.literature else None,
            }]

        user = self.species_checked_by
        user_pk = None
        if user:
            if u := User.objects.filter(username=self.species_checked_by).first():
                user_pk = u.pk
        else:
            user = get_current_user()
            if user:
                user_pk = user.pk
                user = user.username
        audit.append({
            "date": self.species_checked_date or timezone.now().date().isoformat(),
            "user": user,
            "user_pk": user_pk,
            "species": self.species.full_name_generated,
            "species_pk": self.species.pk,
            "literature": self.literature.full_name_generated if self.literature else None,
            "literature_pk": self.literature.pk if self.literature else None,
        })

        for row in audit:
            if hasattr(row["date"], "isoformat"):
                row["date"] = row["date"].isoformat()
        self.species_audit = audit


class IndividualValidateMixin(object):
    """
    Form validation used for Individual and Seed
    """
    @classmethod
    def _update_initial(cls, kwargs: dict):
        """
        Adjust the kwargs["initial"] before passing to ModelForm constructor
        """
        # create same random accession number in two fields when creating a new individual
        initialize_accession = not kwargs.pop("do_not_initialize_accession", False)
        if not kwargs.get("instance") and initialize_accession:
            kwargs.setdefault("initial", {})
            kwargs["initial"]["accession_number"] = kwargs["initial"]["ipen_accession_number"] = (
                get_new_accession_number()
            )

    def clean_ipen_garden_code(self):
        '''
        check ipen_garden_code is set
        '''

        if self.cleaned_data['ipen_garden_code'].code == None:
            self._errors["ipen_garden_code"] = ErrorList([_("The selected garden does not have an IPEN code.")])

        return self.cleaned_data['ipen_garden_code']

    #def clean_ipen_country(self):
    #    '''
    #    check ipen_country is not "UNKNOWN"
    #    '''
    #    if self.cleaned_data['ipen_country'] == "xx":
    #        self._errors["ipen_country"] = ErrorList([_("IPEN Country must not be \"UNKNOWN\"")])
    #
    #    return self.cleaned_data['ipen_country']

    def clean_order_number(self):
        num = self.cleaned_data["order_number"]
        if num is None:
            raise forms.ValidationError(_("Order number must be assigned"), code="invalid")
        if hasattr(self, "instance"):
            Model = self.instance.__class__
            qset = Model.objects.filter(order_number=num).exclude(id=self.instance.id)
            if qset.exists():
                nextnum = get_new_order_number()
                raise forms.ValidationError(_("Order number already exists, next free number is %s") % nextnum,
                                            code="invalid")
        return num


class IndividualForm(
    IndividualValidateMixin,
    AutoCompleteForm(
        Individual,
        widgets={
            "species_audit": SpeciesAuditWidget(),
        #    "accession_number": widgets.NumberInput()  # don't need a spinbox for the accession number
        },
        autocomplete_mapping={
            "came_as_species": {"model": Species, "field": "full_name_generated"},
        }
    )
):
    def __init__(self, *args, **kwargs):
        self._update_initial(kwargs)
        super(IndividualForm, self).__init__(*args, **kwargs)
        if field := self.fields.get("literature"):
            field.widget.attrs["style"] = "width: 40rem;"


class SeedInLatestCatalogFilter(FieldListFilter):
    """
    Filter if seed is in latest seed catalog.

    It's displayed in the changelist filterbox because Django wont process it otherwise,
    but the filterbox is disabled via CSS for the seed changelist
    """
    QUERY_NAME = "seedcatalog"
    CHOICES = [
        ("yes", _("included")),
        ("no", _("not included")),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = _("is in latest catalog")

    def has_output(self):
        return True  # turning this to False unfortunately disables the filter

    def expected_parameters(self):
        return [self.QUERY_NAME]

    def choices(self, changelist):
        param_name = self.expected_parameters()[0]
        yield {
            "selected": self.used_parameters.get(param_name) not in ("yes", "no"),
            "query_string": changelist.get_query_string(remove=[param_name]),
            "display": _("All"),
        }
        for value, text in self.CHOICES:
            yield {
                "selected": self.used_parameters.get(param_name) == value,
                "query_string": changelist.get_query_string({param_name: value}),
                "display": text,
            }

    def queryset(self, request, queryset: QuerySet):
        value = request.GET.get(self.expected_parameters()[0])
        if value is None:
            return queryset

        cat = SeedCatalog.objects.latest_catalog()
        if cat is None:
            if value == self.CHOICES[0][0]:
                return queryset.none()
            else:
                return queryset
        else:
            if value == self.CHOICES[0][0]:
                return queryset.filter(seedcatalog=cat)
            else:
                return queryset.exclude(seedcatalog=cat)

    @classmethod
    def create_header_filter(cls):
        """Return the CustomSelectHeaderFilter used in the ConfigurableTable header"""
        return CustomSelectHeaderFilter(
            query_name=cls.QUERY_NAME,
            choices=cls.CHOICES,
        )


class Seed(Individual):

    class Meta:
        verbose_name = _("seed")
        verbose_name_plural = _("seeds")
        proxy = True

    @configurable
    def family_single(self):
        return self.species.family.family
    family_single.short_description = _('family')
    family_single.admin_order_field = "species__family__family"

    @configurable
    def genus_single(self):
        return self.species.family.genus
    genus_single.short_description = _('genus')
    genus_single.admin_order_field = "species__family__genus"

    @configurable
    def seed_etikett_decorator(self):
        from labels import label_link_decorator
        return label_link_decorator(
            "individual", self.pk, self.ipen_generated
        )
    seed_etikett_decorator.short_description = _("label")
    seed_etikett_decorator.exclude_csv = True

    @configurable
    def nomenclature_checked_decorator(self):
        icon_url = static('admin/img/icon-%s.svg' %
                          {True: 'yes', False: 'no', None: 'unknown'}[self.species.nomenclature_checked])
        return mark_safe(format_html('<img src="{}" alt="{}" />', icon_url, self.species.nomenclature_checked))
    nomenclature_checked_decorator.short_description = _("nomenclature checked")
    nomenclature_checked_decorator.admin_order_field = "species__nomenclature_checked"
    nomenclature_checked_decorator.searchable_field = "species__nomenclature_checked"

    @configurable
    def etikett_detail_decorator(self):
        return self.species.area_of_distribution_background
    etikett_detail_decorator.short_description = _("detailed")
    etikett_detail_decorator.admin_order_field = "species__area_of_distribution_background"
    etikett_detail_decorator.searchable_field = "species__area_of_distribution_background"

    @configurable
    def etikett_text_decorator(self):
        return self.species.area_of_distribution_etikettxt
    etikett_text_decorator.short_description = _("label text")
    etikett_text_decorator.admin_order_field = "species__area_of_distribution_etikettxt"
    etikett_text_decorator.searchable_field = "species__area_of_distribution_etikettxt"

    @configurable
    def etikett_detail_decorator(self):
        return self.species.area_of_distribution_background
    etikett_detail_decorator.short_description = _("detailed")
    etikett_detail_decorator.admin_order_field = "species__area_of_distribution_background"
    etikett_detail_decorator.searchable_field = "species__area_of_distribution_background"

    @configurable
    def seed_add_to_latest_catalog_decorator(self):
        catalog = SeedCatalog.objects.latest_editable_catalog()
        if not catalog:
            url = reverse("admin:seedcatalog_seedcatalog_add")
            return mark_safe('<a href="%s">%s</a>' % (url, _("Create new catalog.")))

        request = get_current_request()
        redirect = escape(request.path)
        if request.GET:
            redirect += "?" + request.GET.urlencode()

        if catalog.seed.filter(pk=self.pk).exists():
            url = reverse("seedcatalog:remove_seed", args=(self.pk, catalog.pk,))
            return_string = '<a title="%s: %s" href="%s?_redirect=%s">%s</a>' % (
                _("catalog"), catalog, url, redirect, _("remove")
            )
        else:
            url = reverse("seedcatalog:add_seed_to_current", args=(self.pk,))
            return_string = '<a title="%s: %s" href="%s?_redirect=%s">%s</a>' % (
                _("catalog"), catalog, url, redirect, _("add")
            )
        return mark_safe(return_string)
    seed_add_to_latest_catalog_decorator.short_description = _('add to current catalog')
    seed_add_to_latest_catalog_decorator.exclude_csv = True
    seed_add_to_latest_catalog_decorator.custom_header_filter = SeedInLatestCatalogFilter.create_header_filter()


class SeedForm(
    IndividualValidateMixin,
    AutoCompleteForm(
        Seed,
        #widgets={
        #    "accession_number": widgets.Input()  # don't need a spinbox for the accession number
        #}
    )
):
    def __init__(self, *args, **kwargs):
        self._update_initial(kwargs)
        super(SeedForm, self).__init__(*args, **kwargs)



# TODO: use or remove
# this basically works but is hard to unify
# and it does not catch the special case of Individual.location_decorator / Outplanting relation
"""
@receiver(post_save)
def generated_fields_updater(sender, **kwargs):
    field_text_dependencies = {
        "BotanicGarden": ("Individual", "ipen_garden_code",),
    }

    if sender.__name__ in field_text_dependencies:
        dep = field_text_dependencies.get(sender.__name__)
        instance = kwargs.get('instance', None)
        print("SAVE", sender, instance, models)

        queries = eval("Individual.objects.filter(%s=instance)" % dep[0])
        for i in dep[1:]:
            queries |= eval("Individual.objects.filter(%s=instance)" % i)
        print(len(queries), queries)
        #print(Individual.objects.filter(ipen_garden_code=instance))
"""
