from django.conf.urls import url

from . import views

app_name = "sidebar"
urlpatterns = [
    url(r'^bookmark/add$', views.add_bookmark, name='add_bookmark'),
    url(r'^bookmark/update_order$', views.update_order, name='update_bookmark_order'),
    url(r'^bookmark/(?P<id>\d+)/delete$', views.delete_bookmark, name='delete_bookmark'),

    url(r'^note/create$', views.create_note, name='new_note'),
    url(r'^note/(?P<id>\d+)/delete$', views.delete_note, name='delete_note'),
    url(r'^note/(?P<id>\d+)/publish/(?P<publish>\d)$', views.publish_note, name='publish_note'),
    url(r'^note/(?P<id>\d+)/edit/$', views.edit_note, name='edit_note'),
]
