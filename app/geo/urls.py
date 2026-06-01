from django.urls import re_path, path

from .views import tile_views

app_name = "geo"
urlpatterns = [
    path('raster-tiles/<int:zoom>/<int:x>/<int:y>.png',  tile_views.raster_tile_cached_view, name='raster_tile_cached_view'),
]
