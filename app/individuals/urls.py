from django.urls import re_path

from . import views

app_name = "individuals"
urlpatterns = [
    re_path(r'^(?P<individualId>\d+)/label/(?P<labelId>\d+)/$', views.generate_label,   name='generate_label'),

    re_path(r'^territory/(?P<forId>\d+)$',                   views.checklist_territory, name='checklist_territory'),
    re_path(r'^department/(?P<forId>\d+)$',                  views.checklist_department,name='checklist_department'),
]
