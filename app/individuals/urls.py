from django.urls import re_path, path

from .views import checklist_views, map_views

app_name = "individuals"
urlpatterns = [
    re_path(r'^territory/(?P<forId>\d+)$',  checklist_views.checklist_territory, name='checklist_territory'),
    re_path(r'^department/(?P<forId>\d+)$', checklist_views.checklist_department,name='checklist_department'),

    re_path(r'^garden-map/', map_views.garden_map_view,   name='garden_map'),
]
