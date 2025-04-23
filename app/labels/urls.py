from django.urls import re_path

from .views import labels, doc

app_name = "labels"

urlpatterns = [
    re_path(r'^individual/(?P<label_pk>\d+)/(?P<indi_pk>\d+)/?$',           labels.label_individual, name='individual'),
    re_path(r'^garden/(?P<label_pk>\d+)/(?P<garden_pk>\d+)/?$',             labels.label_garden, name='garden'),
    re_path(r'^entry/(?P<label_pk>\d+)/(?P<entry_pk>\d+)/?$',               labels.label_entry, name='entry'),

    re_path(r'^random/(?P<label_pk>\d+)/?$',                                labels.label_random, name='random'),
    re_path(r'^random/individual/(?P<label_pk>\d+)/?$',                     labels.label_random_individual, name='random_individual'),
    re_path(r'^random/garden/(?P<label_pk>\d+)/?$',                         labels.label_random_garden, name='random_garden'),
    re_path(r'^random/entry/(?P<label_pk>\d+)/?$',                          labels.label_random_entry, name='random_entry'),

    re_path(r'^docs/template/?$',                                           doc.label_template_doc, name='doc_template'),
]


