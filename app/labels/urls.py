from django.conf.urls import url

from .views import labels, doc

app_name = "labels"

urlpatterns = [
    url(r'^individual/(?P<label_pk>\d+)/(?P<indi_pk>\d+)/?$',           labels.label_individual, name='individual'),
    url(r'^garden/(?P<label_pk>\d+)/(?P<garden_pk>\d+)/?$',             labels.label_garden, name='garden'),

    url(r'^random/(?P<label_pk>\d+)/?$',                                labels.label_random, name='random'),
    url(r'^random/individual/(?P<label_pk>\d+)/?$',                     labels.label_random_individual, name='random_individual'),
    url(r'^random/garden/(?P<label_pk>\d+)/?$',                         labels.label_random_garden, name='random_garden'),

    url(r'^docs/template/?$',                                           doc.label_template_doc, name='doc_template'),
]


