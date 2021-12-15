from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ungettext_lazy
from django.utils.safestring import mark_safe
from django.urls import reverse
from django import forms

from config_tables.admin import Configurable, configurable
from ajax.autocomplete import AutoCompleteForm
from tools import global_request

PROTECTION_OF_SPECIES_CHOICES = (
    ('LC', 'LC (Least Concern)'),
    ('NT', 'NT (Near Threatened)'),
    ('VU', 'VU (Vulnerable)'),
    ('EN', 'EN (Endangered)'),
    ('CR', 'CR (Critically Endangered)'),
    ('EW', 'EW (Extinct in the wild)'),
    ('EX', 'EX (Extinct)'),
)

LIFEFORM_CHOICES = (
    ('P', 'Phanerophyt (Gehölz)'),
    ('C', 'Chamaephyt (Zwergstrauch/Halbstrauch)'),
    ('H', 'Hemikryptophyt (Staude)'),
    ('K', 'Kryptophyt'),
    ('T', 'Therophyt (Einjährige)'),
)


class Family(models.Model, Configurable):
    class Meta:
        verbose_name = _('genus')
        verbose_name_plural = _('genera')
        ordering = ('genus', 'family',)
        unique_together = ('family', 'subfamily', 'tribus', 'subtribus', 'genus', 'genus_author')

    _id_field = "full_name_generated"

    family = models.CharField(verbose_name=_('family'), max_length=50, blank=False)
    subfamily = models.CharField(verbose_name=_('subfamily'), max_length=50, blank=True)
    tribus = models.CharField(verbose_name=_('tribus'), max_length=50, blank=True)
    subtribus = models.CharField(verbose_name=_('subtribus'), max_length=50, blank=True)
    genus = models.CharField(verbose_name=_('genus'), max_length=50, blank=False)
    genus_author = models.CharField(verbose_name=_('author'), max_length=100, blank=True)
    full_name_generated = models.CharField(verbose_name=_('full name'), max_length=350, blank=True)

    # @configurable
    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        if self.family.upper() == 'ASTERACEAE':
            return '%s %s - %s %s %s %s' % (self.genus, self.genus_author, self.family,
                                             self.subfamily, self.tribus, self.subtribus)
        else:
            return '%s %s - %s' % (self.genus, self.genus_author, self.family)

    @configurable
    def change_link_decorator(self):
        url = reverse("admin:species_family_change", args=(self.pk,))
        return mark_safe('<a href="%s" class="changelink">%s</a>' % (url, _('show')))
    change_link_decorator.short_description = _('show')
    change_link_decorator.exclude_csv = True

    @configurable
    def delete_link_decorator(self):
        url = reverse("admin:species_family_delete", args=(self.pk,))
        return mark_safe('<a href="%s" class="deletelink">%s</a>' % (url, _('delete')))
    delete_link_decorator.short_description = _('delete')
    delete_link_decorator.exclude_csv = True

    def save(self, *args, **kwargs):
        if hasattr(self, "full_name_generated"):
            self.full_name_generated = self.get_full_name()
        super(Family, self).save(*args, **kwargs)
        # update coresponding Species.full_name_generated
        if hasattr(Species, "full_name_generated"):
            for i in Species.objects.filter(family=self):
                i.save()


class FamilyForm(AutoCompleteForm(Family)):
    pass


class Species(models.Model, Configurable):

    class Meta:
        verbose_name = ungettext_lazy('species', 'species', 1)
        verbose_name_plural = ungettext_lazy('species', 'species', 2)
        ordering = ('family__genus', 'species', 'subspecies',)
        unique_together = ("family", "species", "species_author", "subspecies", "variety", "form", "cultivar")
        permissions = (("can_check_nomenclature", _("can check nomenclature of a species")),)

    _id_field = 'full_name_generated'

    # SQL:    ALTER TABLE species_species ADD UNIQUE (family, species, species_author, subspecies, variety);

    family = models.ForeignKey(Family, verbose_name=_('genus & family'), on_delete=models.CASCADE)
    species = models.CharField(verbose_name=_('species'), max_length=100, blank=False)
    species_author = models.CharField(verbose_name=_('author species'), max_length=100, blank=True)
    subspecies = models.CharField(verbose_name=_('subspecies'), max_length=100, blank=True)
    subspecies_author = models.CharField(verbose_name=_('author subspec.'), max_length=100, blank=True)
    variety = models.CharField(verbose_name=_('variety'), max_length=200, blank=True)
    variety_author = models.CharField(verbose_name=_('author variety'), max_length=100, blank=True)
    form = models.CharField(verbose_name=_('form'), max_length=200, blank=True)
    form_author = models.CharField(verbose_name=_('author form'), max_length=100, blank=True)
    cultivar = models.CharField(verbose_name=_('cultivar / breed'), max_length=200, blank=True,
                                help_text=_('without quotation marks'))
    full_name_generated = models.CharField(max_length=200, verbose_name=_("full name"), blank=True)
    deutscher_name = models.CharField(max_length=200, verbose_name=_('german name'), blank=True)
    synonyme = models.TextField(verbose_name=_('synonyms'), blank=True, null=True)
    area_of_distribution_etikettxt = models.CharField(verbose_name=_('label text'), max_length=200, blank=True,
                                                      help_text="%")
    area_of_distribution_background = models.TextField(verbose_name=_('detailed'), blank=True)
    protection_of_species = models.CharField(verbose_name=_('endangering'), max_length=2,
                                             choices=PROTECTION_OF_SPECIES_CHOICES, blank=True)
    poisonous_plant = models.BooleanField(verbose_name=_('poisonous plant'), blank=True, null=True)
    lifeform = models.CharField(verbose_name=_('life-form'), max_length=2, choices=LIFEFORM_CHOICES, blank=True)
    nomenclature_checked = models.BooleanField(verbose_name=_('nomenclature checked'), default=False, blank=True,
                                                   null=True)
    comment = models.TextField(verbose_name=_('comment'), max_length=10000, blank=True, null=True)
    picture = models.ImageField(verbose_name=_('picture'), upload_to="pictures", blank=True)

    @configurable
    def get_author_name(self):
        for author in filter(bool, (
            self.variety_author,
            self.subspecies_author,
            self.form_author,
            self.species_author,
        )):
            return author
        return ''
    get_author_name.short_description = _('author name')

    @configurable
    def __str__(self):
        return self.full_name()

    def full_name(self, with_author=True):
        return_string = '%s %s' % (self.family.genus, self.species)
        if self.subspecies:
            return_string += " subsp. " + self.subspecies
        if self.variety:
            return_string += " var. " + self.variety
        if self.form:
            return_string += " f. " + self.form
        if self.cultivar:
            return_string += " \'" + self.cultivar + "\'"
        if with_author:
            author = self.get_author_name()
            if author:
                return_string += " %s" % author
        return return_string

    def full_name_each_author_list(self):
        ret_list = [{"name": '%s %s' % (self.family.genus, self.species)}]
        if self.species_author:
            ret_list.append({"author": self.species_author})
        if self.subspecies:
            ret_list.append({"name": "subsp. %s" % self.subspecies})
            if self.subspecies_author:
                ret_list.append({"author": self.subspecies_author})
        if self.variety:
            ret_list.append({"name": "var. %s" % self.variety})
            if self.variety_author:
                ret_list.append({"author": self.variety_author})
        if self.form:
            ret_list.append({"name": "f. %s" % self.form})
            if self.form_author:
                ret_list.append({"author": self.form_author})
        if self.cultivar:
            ret_list.append({"name": "'%s'" % self.cultivar})
        return ret_list

    def full_name_no_author(self):
        return self.full_name(with_author=False)

    def distribution_lines(self):
        return self.area_of_distribution_etikettxt.split("\n")

    @configurable
    def family_single(self):
        return self.family.family
    family_single.short_description = _('family')
    family_single.admin_order_field = "family__family"

    @configurable
    def genus_single(self):
        return self.family.genus
    genus_single.short_description = _('genus')
    genus_single.admin_order_field = "family__genus"

    @configurable
    def change_link_decorator(self):
        url = reverse("admin:species_species_change", args=(self.pk,))
        return mark_safe('<a href="%s" class="changelink">%s</a>' % (url, _('show')))
    change_link_decorator.short_description = _('show')
    change_link_decorator.exclude_csv = True

    @configurable
    def delete_link_decorator(self):
        url = reverse("admin:species_species_delete", args=(self.pk,))
        return mark_safe('<a href="%s" class="deletelink">%s</a>' % (url, _('delete')))
    delete_link_decorator.short_description = _('delete')
    delete_link_decorator.exclude_csv = True

    @configurable
    def availability_decorator(self):
        url = reverse("species:is_available", args=(self.pk,))
        return mark_safe('<a href="%s">%s</a>' % (url, _('check')))
    availability_decorator.short_description = _('availability')
    availability_decorator.exclude_csv = True

    @configurable
    def search_individuals_link_decorator(self):
        url = reverse("admin:individuals_individual_changelist")
        return mark_safe('<a href="%s?q=%s%%20%s">%s</a>' % (
            url,
            self.family.genus, self.species, _('search individuals')
        ))
    search_individuals_link_decorator.short_description = _('individuals')
    search_individuals_link_decorator.exclude_csv = True

    @configurable
    def search_seeds_link_decorator(self):
        url = reverse("admin:individuals_seed_changelist")
        return mark_safe('<a href="%s?q=%s%%20%s&seed_available__exact=1">%s</a>' % (
            url,
            self.family.genus, self.species, _('search seeds')
        ))
    search_seeds_link_decorator.short_description = _('seeds')
    search_seeds_link_decorator.exclude_csv = True

    def save(self, *args, **kawrgs):
        if hasattr(self, "full_name_generated"):
            self.full_name_generated = self.full_name()
        super(Species, self).save(*args, **kawrgs)

        from individuals.models import Individual
        if hasattr(Individual, "id_name_generated"):
            for i in Individual.objects.filter(species=self):
                i.save()


class SpeciesForm(AutoCompleteForm(Species)):
    def __init__(self, *args, **kwargs):
        super(SpeciesForm, self).__init__(*args, **kwargs)
        if not global_request.get_current_user().has_perm("species.can_check_nomenclature"):
            self.fields["nomenclature_checked"] = forms.NullBooleanField(disabled=True)
