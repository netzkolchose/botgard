from django.conf.urls import url
from django.utils.translation import gettext_lazy as _

from . import views

app_name = "botman"
urlpatterns = [
    url(r'^$',                                      views.index_page,           name='index'),
    url(r'^no_permission$',                         views.no_permission_page,   name='no_permission'),

    url(r'^admin/?',                                views.data_admin_view,      name="data_admin"),

    url(r'^activity/?$',                            views.activity_view,        name='activity'),
]