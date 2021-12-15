from .models import *
from django.contrib import admin
from config_tables.admin import ConfigurableTable, configurable, ForeignKeyFilter
from django.utils.translation import gettext_lazy as _

from tools import readOnlyAdmin


class FamilyAdmin(readOnlyAdmin.ReadPermissionModelAdmin, ConfigurableTable):
    form = FamilyForm
    list_display = ('change_link_decorator', 'family', 'genus', 'genus_author', 'subfamily', 'tribus', 'subtribus',
                    'delete_link_decorator')
    search_fields = ('family', 'genus', 'genus_author', 'subfamily', 'tribus', 'subtribus')
    fieldsets = (
        (None, {
            'fields': ('family', ('subfamily', 'tribus', 'subtribus'), ('genus', 'genus_author')),
        }),
    )

    class Media:
        css = {"screen": (
            '/static/config_tables/searchable_admin_list.css',
            #'/static/config_tables/jquery-ui.min.css',
            )
        }
        js = (
            '/static/species/asteraceae.js',
        )



class SpeciesAdmin(readOnlyAdmin.ReadPermissionModelAdmin, ConfigurableTable):
    form = SpeciesForm
    list_display = (
    'change_link_decorator', #'full_name_generated', '__str__',
    'genus_single', 'family_single',
    'species',
    'deutscher_name', 'synonyme',
    'area_of_distribution_etikettxt',
    'search_individuals_link_decorator', 'search_seeds_link_decorator', 'availability_decorator',
    'delete_link_decorator')
    blacklist = ("id", "__str__")
    list_filter = (#'nomenclature_checked', 'poisonous_plant',
                   ('family__full_name_generated', ForeignKeyFilter),
                   ('family__family', ForeignKeyFilter),
                   ('family__genus', ForeignKeyFilter),
                   )
    search_fields = ['@family__family', '@family__genus', '@species', '@variety', 'synonyme', '@family__subfamily',
                     '@family__tribus', '@family__subtribus', 'deutscher_name', 'cultivar', ]
    save_on_top = True

    fieldsets = (
        (None, {
            'fields': (
            'family',
            ('species', 'species_author'),
            ('subspecies', 'subspecies_author'),
            ('variety', 'variety_author'),
            ('form', 'form_author'),
            'cultivar', 'deutscher_name', 'synonyme')
        }),
        #           ('Asteraceae', {
        #           	'classes' : 'collapse',
        #           	'fields' : ('subfamily', 'tribus', 'subtribus'),
        #          }),
        (_('distribution'), {
            'classes': 'collapse',
            'fields': ('area_of_distribution_etikettxt', 'area_of_distribution_background')
        }),
        (_('additional'), {
            'classes': 'collapse',
            'fields': (
            'protection_of_species', 'poisonous_plant', 'lifeform', 'nomenclature_checked', 'picture', 'comment')
        }),
    )

    class Media:
        js = (
            '/static/species/distribution_text.js',
        )


admin.site.register(Species, SpeciesAdmin)
admin.site.register(Family, FamilyAdmin)
