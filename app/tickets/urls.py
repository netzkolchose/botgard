from django.conf.urls import url

from . import views

app_name = "tickets"
urlpatterns = [
    url(r'^state/(?P<forId>\d+)$',  views.state,            name='state'),
    url(r'^show/(?P<forId>\d+)$',   views.show_ticket,      name='show_ticket'),

    url(r'^set-done/(?P<etikett_individual_pk>\d+)/?$',     views.set_label_done,      name='set_label_done'),
]

