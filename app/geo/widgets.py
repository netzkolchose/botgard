from django.contrib.gis.forms.widgets import BaseGeometryWidget
from django.contrib.gis.geometry import json_regex
from django.conf import settings


def get_botgard_map_template_context(with_polygons: bool = True) -> dict:
    import config_app
    from individuals.models import Territory, Department

    context = {
        "map_srid": 3857,
        "map_tile_url": settings.MAP_TILE_URL,
        "default_location": config_app.get_value("geo_location"),
    }

    if with_polygons:
        context.update({
            "territories": list(
                Territory.objects.all()
                .order_by("code")
                .values(
                    "pk", "code", "name", "polygon",
                )
            ),
            "departments": list(
                Department.objects.all()
                .order_by("full_code")
                .values(
                    "territory__code", "territory__name", "territory__pk",
                    "pk", "code", "name", "full_code", "polygon"
                )
            ),
        })

    return context


class BotGardOpenLayersWidget(BaseGeometryWidget):
    template_name = "geo/openlayers.html"
    map_srid = 3857

    def __init__(self, attrs=None, with_garden_map: bool = False, red_dots: bool = False):
        super().__init__(attrs)
        self._with_garden_map = with_garden_map
        self._red_dots = red_dots

    class Media:
        css = {
            "all": (
                "geo/ol-v10.9.0.css",
                "geo/ol-extra.css",
            )
        }
        js = (
            "geo/ol-v10.9.0.js",
            "geo/OLMapWidget.js",
            "geo/garden_map.js",
        )

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context.update({
            "red_dots": self._red_dots,
            **get_botgard_map_template_context(),
        })
        if self._with_garden_map:
            context.update({
                "with_garden_map": True,
                "form_element_name": name,
            })
        return context

    def serialize(self, value):
        return value.json if value else ""

    def deserialize(self, value):
        geom = super().deserialize(value)
        # GeoJSON assumes WGS84 (4326). Use the map's SRID instead.
        if geom and json_regex.match(value) and self.map_srid != 4326:
            geom.srid = self.map_srid
        return geom
