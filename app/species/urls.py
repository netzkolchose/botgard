from django.conf.urls import url

from . import views

app_name = "species"
urlpatterns = [
    url(r'^available/(?P<forId>\d+)$',      views.is_available, name='is_available'),

    # TODO: use or remove
    #url(r'^ajax/species/autocomplete/(?P<search_item>\w+)/(?P<limit_by>\d+)$',
    #                                        views.ajax_autocomplete_species,    name='ajax_autocomplete_species'),
    #url(r'^ajax/families/autocomplete/(?P<search_item>\w+)/(?P<limit_by>\d+)$',
    #                                        views.ajax_autocomplete_families,   name='ajax_autocomplete_families'),
    #url(r'^ajax/individual/autocomplete/species/(?P<limit_by>\d+)$',
    #                                        views.ajax_autocomplete_individual_species,
    #                                                                            name='ajax_autocomplete_individual_species'),
    #url(r'^ajax/species/name/(?P<forId>\d+)$',
    #                                        views.ajax_name,                    name='ajax_name'),
]
