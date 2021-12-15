import re
from typing import List

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django import forms
from django.db import transaction

from .models import *
from plantimages.admin import PlantImageInline
# from seedcatalog.models import SeedCatalog

from tools import readOnlyAdmin
from config_tables.admin import ConfigurableTable, ForeignKeyFilter
from ajax.autocomplete import AutoCompleteForm
from labels.mass_action import add_label_mass_actions


class DepartmentAdmin(readOnlyAdmin.ReadPermissionModelAdmin, ConfigurableTable):
    form = DepartmentForm
    list_display = ('change_link_decorator', 'territory', 'code', 'name', 'list_link_decorator',
                    'num_individuals_alive', 'num_species_alive',
                    'delete_link_decorator',
                    )
    list_display_links = ()
    list_filter = (('territory__name_generated', ForeignKeyFilter),
                   )
    search_fields = ('code', 'name')
    ordering = ("territory__code", 'code')
    admin_order_field = ("territory__code", "code")
    blacklist = ("id", "__str__", 'full_code',)

    change_form_template = "individuals/change_form_plant_stats.html"

    class Media:
        css = {"screen": ('individuals/change_form_plant_stats.css',)}


class TerritoryAdmin(readOnlyAdmin.ReadPermissionModelAdmin, ConfigurableTable):
    form = TerritoryForm
    list_display = ('change_link_decorator', 'code', 'name', 'list_link_decorator',
                    'num_individuals_alive', 'num_species_alive',
                    'delete_link_decorator')
    list_display_links = ()
    search_fields = ('code', 'name')
    ordering = ('code',)
    blacklist = ("id", "name_generated", )

    change_form_template = "individuals/change_form_plant_stats.html"

    class Media:
        css = {"screen": ('individuals/change_form_plant_stats.css',)}


class OutplantingInline(readOnlyAdmin.ReadOnlyTabularInline):
    #form = AutoCompleteForm(Outplanting)
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
    list_filter = (# 'seed_available', 'seed_in_stock', 'source__name',
                   ('species__full_name_generated', ForeignKeyFilter),
                   ('species__nomenclature_checked', ForeignKeyFilter),
                   ('species__area_of_distribution_etikettxt', ForeignKeyFilter),
                   ('species__area_of_distribution_background', ForeignKeyFilter),
                   ('species__family__family', ForeignKeyFilter),
                   ('species__family__genus', ForeignKeyFilter),
                   )

    blacklist = ('id', '__str__', 'ipen_transfer_restricted', 'ipen_garden_code', 'ipen_accession_number',
                 'ipen_country', 'departments_generated', 'territories_generated', 'species',
                 'alive_outplantings_generated')

    search_fields = ['order_number', '@species__species', 'accession_number', '@species__family__genus',
                     '@species__family__family', 'ipen_generated', '@source__name', '@species__deutscher_name']
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
        css = {"screen": ('BotGard/css_dropdown/css_dropdown.css',)}

    def get_search_results(self, request, queryset, search_term):
        order_ids = get_seed_order_ids(search_term)
        if not order_ids:
            return super().get_search_results(request, queryset, search_term)

        return queryset.filter(order_number__in=order_ids), False

    def get_actions(self, request):
        actions = super().get_actions(request)
        add_label_mass_actions(request, actions, "individual")
        return actions


def get_seed_order_ids(s: str) -> List[str]:
    return re.findall(r"\d+", s)


class IndividualAdmin(readOnlyAdmin.ReadPermissionModelAdmin, ConfigurableTable):
    form = IndividualForm
    save_on_top = True
    list_display = (
        'change_link_decorator', 'accession_number', 'accession_extension', 'ipen_generated',
        #'sowing_number',
        'species_link_decorator',
        'departments_decorator', 'is_alive', 'source', 'etikett_link_decorator',
    )
    list_filter = (#'seed_available', 'seed_in_stock',
                   #'species__nomenclature_checked',
                   # add all foreignkey fields that should be filterable
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
                 'outplantings_generated', 'alive_outplantings_generated', 'is_alive_generated')

    list_display_links = ()
    search_fields = ('accession_number', 'ipen_generated',
                     '@species__species',
                     '@species__subspecies',
                     '@species__variety',
                     '@species__form',
                     '@species__family__genus',
                     '@species__family__family',
                     '@species__full_name_generated',
                     '@species__deutscher_name',
                     '@source__name',
                     )
    ordering = ('accession_number',)
    fieldsets = (
        (None, {
            'fields': (('accession_number', 'accession_extension', 'seed_available', 'seed_in_stock',),
                       ('species', 'species_checked_by', 'came_as_species'),)
        }),
        ('IPEN', {
            'fields': (('ipen_country', 'ipen_transfer_restricted', 'ipen_garden_code', 'ipen_accession_number'),)
        }),
        (_('habitat'), {
            'fields': (('found_country',), 'found_text', ('collector_name', 'collector_number', 'collector_date'),)
        }),
        (_('source'), {
            'fields': (('source', 'source_date', 'came_in_as'),)
        }),
        (_('miscellaneous'), {
            'classes': 'collapse',
            'fields': ('gender', 'comment',)
        }),
        (_('seeds'), {
            'fields': ('order_number', 'sowing_number')
        })
    )
    raw_id_fields = ("species",)
    inlines = [OutplantingInline, PlantImageInline]

    class Media:
        css = {"screen": ('BotGard/css_dropdown/css_dropdown.css',)}

    def get_actions(self, request):
        actions = super().get_actions(request)
        add_label_mass_actions(request, actions, "individual")
        return actions


admin.site.register(Individual, IndividualAdmin)
admin.site.register(Seed, SeedAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Territory, TerritoryAdmin)


# TODO: Outplantings can be part of admin but should be read-only!
if 0:
    class OutplantingAdmin(readOnlyAdmin.ReadPermissionModelAdmin, ConfigurableTable):
        form = AutoCompleteForm(Outplanting)
        list_display = ('territory_decorator', 'department_decorator',
                        'seeded_date', 'date', 'plant_died',
                        'individual_link_decorator', 'family_single', 'genus_single')
        list_filter = (
            ('department__code', ForeignKeyFilter),
            ('department__territory__code', ForeignKeyFilter),
                       # ('individual__species', ForeignKeyFilter),
        )
        blacklist = ('id', 'individual', 'department')
    admin.site.register(Outplanting, OutplantingAdmin)