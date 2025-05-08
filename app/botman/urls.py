from django.urls import re_path

from . import views

app_name = "botman"
urlpatterns = [
    re_path(r'^$',                                      views.index_page,           name='index'),
    re_path(r'^no_permission$',                         views.no_permission_page,   name='no_permission'),

    re_path(r'^admin/?',                                views.data_admin_view,      name="data_admin"),

    re_path(r'^activity/?$',                            views.activity_view,        name='activity'),
]