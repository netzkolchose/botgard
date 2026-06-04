from django.contrib.gis.forms.widgets import OpenLayersWidget
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


class BotGardOpenLayersWidget(OpenLayersWidget):
    template_name = "geo/openlayers.html"

    def __init__(self, attrs=None, with_garden_map: bool = False, red_dots: bool = False):
        super().__init__(attrs)
        self._with_garden_map = with_garden_map
        self._red_dots = red_dots

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
