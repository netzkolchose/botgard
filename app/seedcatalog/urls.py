from django.urls import re_path

from . import views

app_name = "seedcatalog"
urlpatterns = [
    re_path(r'^edit/(?P<forId>\d+)$',                               views.edit_seeds, name='edit_seeds'),
    re_path(r'^add/(?P<seedId>\d+)/to/(?P<catalogId>\d+)/$',        views.add_seed_to_catalog, name='add_seed'),
    re_path(r'^add/(?P<seedId>\d+)/toCurrent/$',                    views.add_seed_to_current_catalog, name='add_seed_to_current'),
    re_path(r'^remove/(?P<seedId>\d+)/from/(?P<catalogId>\d+)/$',   views.remove_seed_from_catalog, name='remove_seed'),
    re_path(r'^remove-all-seeds/(?P<catalogId>\d+)/$',              views.remove_all_seeds_from_catalog, name='remove_all_seeds'),
    re_path(r'^generate/(?P<catalogId>\d+)/$',                      views.generate_request, name='generate'),
    re_path(r'^debug/(?P<catalogId>\d+)/$',                         views.debug_view, name='debug'),
    re_path(r'^duplicate/(?P<catalogId>\d+)/$',                     views.duplicate_catalog_request, name="duplicate_catalog"),
    re_path(r'^finalize/(?P<catalogId>\d+)/$',                      views.finalize_catalog_request, name="finalize_catalog"),
]
