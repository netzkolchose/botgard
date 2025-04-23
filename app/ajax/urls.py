from django.urls import re_path

from . import views

app_name = "ajax"
urlpatterns = [
    re_path(r'^model/model.json/?$',            views.model_fieldvalues_json, name='model_json'),
    re_path(r'^model/choices.json/?$',          views.choice_fieldvalues_json, name='choices_json'),
]
