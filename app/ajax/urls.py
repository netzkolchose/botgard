from django.conf.urls import url

from . import views

app_name = "ajax"
urlpatterns = [
    url(r'^model/model.json/?$',            views.model_fieldvalues_json, name='model_json'),
    url(r'^model/choices.json/?$',          views.choice_fieldvalues_json, name='choices_json'),
]
