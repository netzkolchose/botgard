from django.conf.urls import url

from .views import labels, doc

app_name = "labels"

urlpatterns = [
    url(r'^individual/(?P<label_pk>\d+)/(?P<indi_pk>\d+)/?$',           labels.label_individual, name='individual'),
    url(r'^garden/(?P<label_pk>\d+)/(?P<garden_pk>\d+)/?$',             labels.label_garden, name='garden'),
    url(r'^entry/(?P<label_pk>\d+)/(?P<entry_pk>\d+)/?$',               labels.label_entry, name='entry'),

    url(r'^random/(?P<label_pk>\d+)/?$',                                labels.label_random, name='random'),
    url(r'^random/individual/(?P<label_pk>\d+)/?$',                     labels.label_random_individual, name='random_individual'),
    url(r'^random/garden/(?P<label_pk>\d+)/?$',                         labels.label_random_garden, name='random_garden'),
    url(r'^random/entry/(?P<label_pk>\d+)/?$',                          labels.label_random_entry, name='random_entry'),

    url(r'^docs/template/?$',                                           doc.label_template_doc, name='doc_template'),
]


