from django.urls import re_path

from . import views

app_name = "tickets"
urlpatterns = [
    re_path(r'^state/(?P<forId>\d+)$',  views.state,            name='state'),
    re_path(r'^show/(?P<forId>\d+)$',   views.show_ticket,      name='show_ticket'),

    re_path(r'^set-done/(?P<etikett_individual_pk>\d+)/?$',     views.set_label_done,      name='set_label_done'),
]
