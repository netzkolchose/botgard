from django.urls import re_path

from . import views

app_name = "sidebar"
urlpatterns = [
    re_path(r'^bookmark/add$', views.add_bookmark, name='add_bookmark'),
    re_path(r'^bookmark/update_order$', views.update_order, name='update_bookmark_order'),
    re_path(r'^bookmark/(?P<id>\d+)/delete$', views.delete_bookmark, name='delete_bookmark'),

    re_path(r'^note/create$', views.create_note, name='new_note'),
    re_path(r'^note/(?P<id>\d+)/delete$', views.delete_note, name='delete_note'),
    re_path(r'^note/(?P<id>\d+)/publish/(?P<publish>\d)$', views.publish_note, name='publish_note'),
    re_path(r'^note/(?P<id>\d+)/edit/$', views.edit_note, name='edit_note'),
]
