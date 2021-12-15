from django.db import models, OperationalError
from django import forms
from django.forms import widgets
from django.forms.utils import ErrorList
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ungettext_lazy as __
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



class Individual(models.Model, Configurable):

    class Meta:
        verbose_name = _("individual")
        verbose_name_plural = _("individuals")
        unique_together = ("ipen_country", "ipen_transfer_restricted", "ipen_accession_number", "ipen_garden_code")

    _id_field = "id_name_generated"

    #def __init__(self, *arg, **kwargs):
    #    super(Individual, self).__init__(*arg, **kwargs)
    #    self.register_generated_field("ipen_generated", ("ipen_garden_code",))

    accession_number = models.IntegerField(verbose_name=_("accession #"), blank=False, null=True, db_index=True,
                                           default=get_new_accession_number, unique=True)
    accession_extension = models.CharField(max_length=2, verbose_name=_("code of origin"),
                                           choices=ACCESSION_EXTENSION_CHOICES, blank=True, null=True)
    species = models.ForeignKey('species.Species', verbose_name=_("genus & Species"), blank=False,
                                on_delete=models.CASCADE)

    id_name_generated = models.CharField(max_length=100, verbose_name=_("name"),
                                         default="", editable=False)

    species_checked_by = models.CharField(max_length=100, verbose_name=_("plant categorized by"), blank=True)

    came_as_species = models.CharField(max_length=100, verbose_name=_("received as species"), blank=True)

    ipen_country = models.CharField(max_length=3, choices=ISO_COUNTRY_CHOICES, verbose_name="IPEN", db_index=True)
    ipen_transfer_restricted = models.CharField(max_length=1, choices=IPEN_TRANSFER_RESTRICTIONS, verbose_name="-")
    ipen_garden_code = models.ForeignKey('botman.BotanicGarden', verbose_name="-", on_delete=models.CASCADE)
    ipen_accession_number = models.CharField(max_length=50, verbose_name="-")

    source = models.ForeignKey('botman.BotanicGarden', related_name="source_key", verbose_name=_("source"), blank=True,
                               null=True, on_delete=models.CASCADE)
    source_date = models.DateField(verbose_name=_("date of receipt"), blank=True, null=True)
    came_in_as = models.CharField(max_length=2, choices=CAME_IN_AS_CHOICES, verbose_name=_("received as"), blank=True,
                                  db_index=True)

    found_country = models.CharField(max_length=3, choices=ISO_COUNTRY_CHOICES, verbose_name=_("collecting country"),
                                     blank=False, db_index=True)
    found_text = models.TextField(max_length=10000, verbose_name=_("collecting place description"), blank=True)
    collector_name = models.CharField(max_length=100, verbose_name=_("collector's name"), blank=True, null=False)
    collector_number = models.CharField(max_length=100, verbose_name=_("collection number"), blank=True)
    collector_date = models.DateField(verbose_name=_("collection date"), blank=True, null=True)

    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name=_("gender"), blank=True)
    comment = models.TextField(max_length=10000, verbose_name=_("comment"), blank=True)

    ipen_generated = models.CharField(max_length=200, editable=False, null=True,
                                      verbose_name="IPEN")  # help field for searching and sorting for ipen

    seed_available = models.BooleanField(verbose_name=_("seed available"))
    order_number = models.IntegerField(verbose_name=_("order number"), unique=True, default=get_new_order_number)

    seed_collector_date = models.DateField(verbose_name=_("seed's collection date"), blank=True, null=True)
    seed_in_stock = models.BooleanField(verbose_name=_("seed in stock"))

    # list of PKs of Outplanting
    alive_outplantings_generated = PickledObjectField(verbose_name=_("alive_outplantings_generated"),
                                                      default=None, blank=True, null=True)
    outplantings_generated = PickledObjectField(verbose_name=_("outplantings_generated"),
                                                default=None, blank=True, null=True)

    # department codes as text
    departments_generated = models.CharField(max_length=1000, verbose_name=_("departments"), blank=True)
    # territory codes as text
    territories_generated = models.CharField(max_length=1000, verbose_name=_("territories"), blank=True)

    sowing_number = models.CharField(verbose_name=_("sowing number"), max_length=100, blank=True)
    is_alive_generated = models.BooleanField(verbose_name=_("is alive"), editable=False, default=False)

    # geo_location = models.ForeignKey("geolocation.GeoLocation", verbose_name=_("location (geonames)"),
    #                                  default=undefined_geolocation,
    #                                  on_delete=models.SET_DEFAULT)

    # osm_location = models.ForeignKey("geolocation.OsmLocation", verbose_name=_("location (osm)"),
    #                                  default=undefined_osmlocation,
    #                                  on_delete=models.SET_DEFAULT)

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
        locations = Outplanting.objects.filter(individual=self.pk)
        locations_alive = locations.filter(plant_died=None)

        self.outplantings_generated = [t[0] for t in locations.values_list("id")]
        self.alive_outplantings_generated = [t[0] for t in locations_alive.values_list("id")]
        self.departments_generated = " ".join(sorted(set(
            l.department.full_code for l in locations if l.department)))
        self.territories_generated = " ".join("(%s)" % i for i in
            sorted(set(l.department.territory.code for l in locations if l.department and l.department.territory)))
        self.is_alive_generated = locations_alive.count() > 0
        if do_save:
            self.save()

    def get_outplantings(self, alive_only=True):
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
    def __str__(self):
        return self.id_name_generated
    __str__.admin_order_field = 'id_name_generated'
    __str__.short_description = _('Individual')

    @configurable
    def change_link_decorator(self):
        return _("show")

    change_link_decorator.short_description = _("show")
    change_link_decorator.exclude_csv = True

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
    def delete_link_decorator(self):
        url = reverse("admin:individuals_individual_delete", args=(self.pk,))
        return mark_safe('<a href="%s" class="deletelink">%s</a>' % (url, _("delete")))

    delete_link_decorator.short_description = _("delete")
    delete_link_decorator.exclude_csv = True

    @configurable
    def etikett_link_decorator(self):
        from labels import label_link_decorator
        return label_link_decorator(
            "individual", self.pk, self.ipen_generated
        )

    etikett_link_decorator.short_description = _("create label")
    etikett_link_decorator.exclude_csv = True

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

    def country_decorator(self):
        """Only needed by geolocation template"""
        cc = self.found_country
        for i in ISO_COUNTRY_CHOICES:
            if i[0] == cc:
                return i[1]
        return cc.upper()

    def found_text_lines(self):
        return self.found_text.split("\n")

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

    def save(self, *args, **kwargs):
        # order number: TODO: XXX Do not change order numbers on save !!
        # self.order_number = Individual.objects.all().order_by('-order_number')[0].order_number + 1 | 0
        # self.order_number = Individual.objects.all().aggregate(models.Max('order_number')).values()[0] or 1000
        # -- update generated fields --
        self.ipen_generated = str.upper(self.ipen_country) + "-" + str.upper(self.ipen_transfer_restricted) + "-" + str.upper(
            self.ipen_garden_code.code) + "-" + str(self.ipen_accession_number)
        # -- update id_name_generated --
        self.id_name_generated = ("%s (%s)" % (self.accession_number,
                                               self.species.full_name(with_author=False))
                                  )[:100]
        # -- save Individual --
        super(Individual, self).save(*args, **kwargs)


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
        if not kwargs.get("instance"):
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
    AutoCompleteForm(Individual, widgets={
        "accession_number": widgets.NumberInput()  # don't need a spinbox for the accession number
    })
):
    def __init__(self, *args, **kwargs):
        self._update_initial(kwargs)
        super(IndividualForm, self).__init__(*args, **kwargs)


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

    def seed_add_to_latest_catalog_decorator(self):
        try:
            catalog = SeedCatalog.objects.latest('pk')
            assert not catalog.is_finalized
        except:
            url = reverse("admin:seedcatalog_seedcatalog_add")
            return mark_safe('<a href="%s">%s</a>' % (url, _("Create new catalog.")))

        request = get_current_request()
        redirect = escape(request.path)
        if request.GET:
            redirect += "?" + request.GET.urlencode()

        if catalog.seed.filter(pk=self.pk):
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


class SeedForm(
    IndividualValidateMixin,
    AutoCompleteForm(Seed, widgets={
        "accession_number": widgets.Input()  # don't need a spinbox for the accession number
    })
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
