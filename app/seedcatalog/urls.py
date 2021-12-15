from django.conf.urls import url

from . import views

app_name = "seedcatalog"
urlpatterns = [
    url(r'^edit/(?P<forId>\d+)$',                               views.edit_seeds, name='edit_seeds'),
    url(r'^add/(?P<seedId>\d+)/to/(?P<catalogId>\d+)/$',        views.add_seed_to_catalog, name='add_seed'),
    url(r'^add/(?P<seedId>\d+)/toCurrent/$',                    views.add_seed_to_current_catalog, name='add_seed_to_current'),
    url(r'^remove/(?P<seedId>\d+)/from/(?P<catalogId>\d+)/$',   views.remove_seed_from_catalog, name='remove_seed'),
    url(r'^generate/(?P<catalogId>\d+)/$',                      views.generate_request, name='generate'),
    url(r'^debug/(?P<catalogId>\d+)/$',                         views.debug_view, name='debug'),
    url(r'^duplicate/(?P<catalogId>\d+)/$',                     views.duplicate_catalog_request, name="duplicate_catalog"),
    url(r'^finalize/(?P<catalogId>\d+)/$',                      views.finalize_catalog_request, name="finalize_catalog"),
]
