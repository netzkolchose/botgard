from django.urls import re_path

from . import views

app_name = "species"
urlpatterns = [
    re_path(r'^available/(?P<forId>\d+)$',      views.is_available, name='is_available'),

    # TODO: use or remove
    #re_path(r'^ajax/species/autocomplete/(?P<search_item>\w+)/(?P<limit_by>\d+)$',
    #                                        views.ajax_autocomplete_species,    name='ajax_autocomplete_species'),
    #re_path(r'^ajax/families/autocomplete/(?P<search_item>\w+)/(?P<limit_by>\d+)$',
    #                                        views.ajax_autocomplete_families,   name='ajax_autocomplete_families'),
    #re_path(r'^ajax/individual/autocomplete/species/(?P<limit_by>\d+)$',
    #                                        views.ajax_autocomplete_individual_species,
    #                                                                            name='ajax_autocomplete_individual_species'),
    #re_path(r'^ajax/species/name/(?P<forId>\d+)$',
    #                                        views.ajax_name,                    name='ajax_name'),
]
