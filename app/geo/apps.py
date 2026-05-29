from django.utils.translation import gettext_lazy as _
from django.apps import AppConfig
from django.contrib.gis.geos import Point

import config_app


class GeoConfig(AppConfig):
    name = 'geo'
    verbose_name = _("Geo locations")


config_app.register_key(
    "geo_location",
    Point(11.585692137454766, 50.93114244279311, srid=4326),
    _("The geo location of the botanic garden"),
)
