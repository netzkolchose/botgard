from django.conf.urls import url

from . import views

app_name = "individuals"
urlpatterns = [
    url(r'^(?P<individualId>\d+)/label/(?P<labelId>\d+)/$', views.generate_label,   name='generate_label'),

    url(r'^territory/(?P<forId>\d+)$',                   views.checklist_territory, name='checklist_territory'),
    url(r'^department/(?P<forId>\d+)$',                  views.checklist_department,name='checklist_department'),
]
