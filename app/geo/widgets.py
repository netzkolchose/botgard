from django.contrib.gis.forms.widgets import OpenLayersWidget
from django.conf import settings
import config_app


class BotGardOpenLayersWidget(OpenLayersWidget):
    template_name = "geo/openlayers.html"

    class Media:
        css = {
            "all": (
                "geo/ol-v7.2.2.css",
                "gis/css/ol3.css",
            )
        }
        js = (
            "geo/ol-v7.2.2.js",
            "geo/OLMapWidget.js",
        )

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context.update({
            "map_tile_url": settings.MAP_TILE_URL,
            "default_location": config_app.get_value("geo_location"),
        })
        return context
