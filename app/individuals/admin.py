import re
from typing import List, Type

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django import forms
from django.db import transaction

from .models import *
from plantimages.admin import PlantImageInline

from tools import readOnlyAdmin
from tools.search_fields import search_fields_compatible
from config_tables.admin import ConfigurableTable, ForeignKeyFilter
from ajax.autocomplete import AutoCompleteForm
from labels.mass_action import add_label_mass_actions
from herbaria.models.specimen import HerbariumSpecimen, create_herbarium_specimen_form_class
from .actions import add_seed_catalog_actions
from .models.individual import SeedInLatestCatalogFilter


class DepartmentAdmin(readOnlyAdmin.ReadPermissionModelAdmin, ConfigurableTable):
    form = DepartmentForm
    list_display = ('change_link_decorator', 'territory', 'code', 'name', 'list_link_decorator',
                    'num_individuals_alive', 'num_species_alive',
                    'delete_link_decorator',
                    )
    list_display_links = ()
    list_filter = (('territory__name_generated', ForeignKeyFilter),
                   )
    search_fields = search_fields_compatible(('code', 'name'))
    ordering = ("territory__code", 'code')
    admin_order_field = ("territory__code", "code")
    blacklist = ("id", "__str__",)

    change_form_template = "individuals/change_form_plant_stats.html"

    class Media:
        css = {"screen": ('individuals/change_form_plant_stats.css',)}


class TerritoryAdmin(readOnlyAdmin.ReadPermissionModelAdmin, ConfigurableTable):
    form = TerritoryForm
    list_display = ('change_link_decorator', 'code', 'name', 'list_link_decorator',
                    'num_individuals_alive', 'num_species_alive',
                    'delete_link_decorator')
    list_display_links = ()
    search_fields = search_fields_compatible(('code', 'name'))
    ordering = ('code',)
    blacklist = ("id", "name_generated", )

    change_form_template = "individuals/change_form_plant_stats.html"

    class Media:
        css = {"screen": ('individuals/change_form_plant_stats.css',)}


class OutplantingInline(readOnlyAdmin.ReadOnlyTabularInline):
    form = OutplantingForm
    model = Outplanting
    min_num = 0


class SeedAdmin(readOnlyAdmin.ReadPermissionModelAdmin, ConfigurableTable):
    form = SeedForm
    save_on_top = True
    actions_on_top = True
    list_display = (
        'change_link_decorator', 'order_number', 'accession_number', 'accession_extension', 'ipen_generated',
        'species_link_decorator', 'seed_available', 'seed_in_stock', 'seed_add_to_latest_catalog_decorator',
        'seed_etikett_decorator', 'endangering_decorator')
    list_filter = (
        # 'seed_available', 'seed_in_stock', 'source__name',
        ('species__full_name_generated', ForeignKeyFilter),
        ('species__nomenclature_checked', ForeignKeyFilter),
        ('species__area_of_distribution_etikettxt', ForeignKeyFilter),
        ('species__area_of_distribution_background', ForeignKeyFilter),
        ('species__family__family', ForeignKeyFilter),
        ('species__family__genus', ForeignKeyFilter),
        (SeedInLatestCatalogFilter.QUERY_NAME, SeedInLatestCatalogFilter),
    )

    blacklist = ('id', '__str__', 'ipen_transfer_restricted', 'ipen_garden_code', 'ipen_accession_number',
                 'ipen_country', 'departments_generated', 'territories_generated', 'species',
                 'outplantings_generated', 'alive_outplantings_generated', 'is_alive_generated',)

    search_fields = search_fields_compatible([
        'order_number', '@species__species', 'accession_number', '@species__family__genus',
        '@species__family__family', 'ipen_generated', '@source__name', '@species__deutscher_name'
    ])
    ordering = ('accession_number',)
    list_editable = ('seed_available', 'seed_in_stock')
    fieldsets = (
        (None, {
            'fields': (('accession_number', 'accession_extension', 'seed_available', 'seed_in_stock',),
                       ('species', 'species_checked_by', 'came_as_species'),)
        }),
        (_('IPEN'), {
            'fields': (('ipen_country', 'ipen_transfer_restricted', 'ipen_garden_code', 'ipen_accession_number'),)
        }),
        (_('habitat'), {
            'fields': (('found_country'), 'found_text', ('collector_name', 'collector_number', 'collector_date'),)
        }),
        (_('source'), {
            'fields': (('source', 'source_date', 'came_in_as'),)
        }),
        (_('miscellaneous'), {
            'classes': 'collapse',
            'fields': ('gender', 'comment')
        }),
        (_('seeds'), {
            'fields': ('order_number',)
        })
    )
    #   	raw_id_fields = ("species", "came_as_species", )
    raw_id_fields = ("species",)
    inlines = [OutplantingInline]

    class Media:
        css = {"screen": (
            'BotGard/css_dropdown/css_dropdown.css',
            'BotGard/css/no-changelist-filter-box.css',
        )}

    def get_search_results(self, request, queryset, search_term):
        order_ids = get_seed_order_ids(search_term)
        if not order_ids:
            return super().get_search_results(request, queryset, search_term)

        return queryset.filter(order_number__in=order_ids), False

    def get_actions(self, request):
        actions = {}
        add_seed_catalog_actions(request, actions)
        add_label_mass_actions(request, actions, "individual")
        actions.update(super().get_actions(request))
        return actions


def get_seed_order_ids(s: str) -> List[str]:
    return re.findall(r"\d+", s)


class HerbariumSpecimenInline(readOnlyAdmin.ReadOnlyTabularInline):
    form = create_herbarium_specimen_form_class(
        # remove one of the defaults, otherwise user might click "add specimen"
        # and all defaults might be exactly the ones the user wants to enter
        # and nothing is saved, because django thought nothing was entered
        no_default_specimen_type=True,
        widgets={
            "comment": forms.TextInput,  # don't use textarea in inline form
        }
    )
    model = HerbariumSpecimen
    min_num = 0
    extra = 0


class IndividualAdmin(readOnlyAdmin.ReadPermissionModelAdmin, ConfigurableTable):
    form = IndividualForm
    save_on_top = True
    list_display = (
        'change_link_decorator', 'accession_number', 'accession_extension', 'ipen_generated',
        #'sowing_number',
        'species_link_decorator',
        'departments_decorator', 'is_alive', 'source', 'etikett_link_decorator',
    )
    list_filter = (
        #'seed_available', 'seed_in_stock',
        #'species__nomenclature_checked',
        # add all foreignkey fields that should be filterable
        ('user__username', ForeignKeyFilter),
        ('source__full_name_generated', ForeignKeyFilter),
        ('species__full_name_generated', ForeignKeyFilter),
        ('species__nomenclature_checked', ForeignKeyFilter),
        ('species__protection_of_species', ForeignKeyFilter),
        ('species__area_of_distribution_etikettxt', ForeignKeyFilter),
        ('species__area_of_distribution_background', ForeignKeyFilter),
        ('species__family__family', ForeignKeyFilter),
        ('species__family__genus', ForeignKeyFilter),
        # ('geo_location__geo_name', ForeignKeyFilter),
        # ('osm_location__full_name', ForeignKeyFilter),
    )

    blacklist = ('id', '__str__', 'ipen_transfer_restricted', 'ipen_garden_code', 'ipen_accession_number',
                 'ipen_country', 'departments_generated', 'territories_generated', 'species',
                 'outplantings_generated', 'alive_outplantings_generated', 'is_alive_generated',)

    list_display_links = ()
    search_fields = search_fields_compatible(('accession_number', 'ipen_generated',
                     '@species__species',
                     '@species__subspecies',
                     '@species__variety',
                     '@species__form',
                     '@species__family__genus',
                     '@species__family__family',
                     '@species__full_name_generated',
                     '@species__deutscher_name',
                     '@source__name',
                     ))
    ordering = ('accession_number',)
    fieldsets = (
        (None, {
            'fields': (('accession_number', 'accession_extension', 'seed_available', 'seed_in_stock',),
                       ('species', 'species_checked_by', 'species_checked_date', 'came_as_species'),)
        }),
        ('IPEN', {
            'fields': (('ipen_country', 'ipen_transfer_restricted', 'ipen_garden_code', 'ipen_accession_number'),)
        }),
        (_('habitat'), {
            'fields': (('found_country',), 'found_text', ('collector_name', 'collector_number', 'collector_date'),)
        }),
        (_('source'), {
            'fields': (('source', 'source_date', 'came_in_as', 'external_order_number'),)
        }),
        (_('miscellaneous'), {
            'classes': 'collapse',
            'fields': ('gender', 'comment', 'import_reference')
        }),
        (_('seeds'), {
            'fields': ('order_number', 'sowing_number')
        })
    )
    raw_id_fields = ("species",)
    inlines = [OutplantingInline, PlantImageInline, HerbariumSpecimenInline]

    class Media:
        css = {"screen": ('BotGard/css_dropdown/css_dropdown.css',)}
        js = (
            "individuals/change_form_tools.js",
        )

    def get_actions(self, request):
        actions = super().get_actions(request)
        add_label_mass_actions(request, actions, "individual")
        return actions


admin.site.register(Individual, IndividualAdmin)
admin.site.register(Seed, SeedAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Territory, TerritoryAdmin)


# ------- below is for transfer from entrybook.Entry to inidividuals.Individual and Outplanting ------


class OutplantingAlwaysChangedForm(forms.ModelForm):
    """
    ModelForm for Outplanting inline to mark
    the initial data from entrybook.Entry as changed.
    """
    class Meta:
        model = Outplanting
        fields = '__all__'

    def has_changed(self):
        return bool(self.initial.get("department"))


class OutplantingAlwaysChangedInline(OutplantingInline):
    form = OutplantingAlwaysChangedForm


class IndividualFromEntryAdmin(IndividualAdmin):
    """
    Special ModelAdmin that creates an
    Individual form and formsets
    from an entrybook.models.Entry instance
    """
    inlines = [OutplantingAlwaysChangedInline, PlantImageInline]

    def __init__(self, model, admin_class, entry_pk):
        from entrybook.models import Entry

        super().__init__(model, admin_class)
        self._entry_pk = entry_pk
        self._entry = Entry.objects.get(pk=self._entry_pk)

    def get_changeform_initial_data(self, request):
        """
        Set the initial values for Individual Form from the Entry instance.
        (not including inline FormSets)
        """
        entry_values = {
            field.name: getattr(self._entry, field.name)
            for field in self._entry._meta.fields
            if hasattr(Individual, field.name)
        }
        return entry_values

    def get_form(self, request, obj=None, change=False, **kwargs):
        """
        Return a Form class that does NOT initialize the
        accession number. It's already stored in the Entry instance
        """
        Form = super().get_form(request, obj, change, **kwargs)

        class PatchedForm(Form):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs, do_not_initialize_accession=True)

        return PatchedForm

    def get_formsets_with_inlines(self, request, obj=None):
        """
        Replace the FormSet class for the OutplantingInline
        with a class that initializes all values
        """
        from django.forms import BaseModelFormSet

        for form_set_class, inline_instance in super().get_formsets_with_inlines(request, obj):
            form_set_class: Type[BaseModelFormSet]

            if isinstance(inline_instance, OutplantingInline):
                entry = self._entry

                class PatchedFormSet(form_set_class):
                    def __init__(self, *args, **kwargs):
                        kwargs["initial"] = [{
                            "department": str(entry.department.pk) if entry.department else None,
                            "seeded_date": entry.seeded_date,
                            "date": entry.bed_out_date,
                        }]
                        super().__init__(*args, **kwargs)

                    def has_changed(self):
                        return True

                form_set_class = PatchedFormSet

            yield form_set_class, inline_instance


class OutplantingAdmin(readOnlyAdmin.ReadPermissionModelAdmin, ConfigurableTable):
    form = OutplantingForm
    list_display = (
        'change_link_decorator',
        'territory_decorator', 'department_decorator',
        'seeded_date', 'date', 'plant_died',
        'individual_link_decorator', 'family_single', 'genus_single',
    )
    list_filter = (
        ('department__code', ForeignKeyFilter),
        ('department__territory__code', ForeignKeyFilter),
        # ('individual__species', ForeignKeyFilter),
    )
    blacklist = ('id', 'individual', 'department')
admin.site.register(Outplanting, OutplantingAdmin)
