from django.urls import re_path, path

from .views import tile_views, map_views

app_name = "geo"
urlpatterns = [
    re_path(r'^garden-map/', map_views.garden_map_view,   name='garden_map'),

    path('raster-tiles/<int:zoom>/<int:x>/<int:y>.png',  tile_views.raster_tile_cached_view, name='raster_tile_cached_view'),
]
