import json
from typing import List, Union, Optional

from django.template import Engine
from django.utils.html import mark_safe
from django.contrib.gis import geos


MAP_COLUMN_CSS = (
    "geo/ol-v10.9.0.css",
    "geo/ol-extra.css",
)

MAP_COLUMN_JS = (
    "geo/ol-v10.9.0.js",
    "geo/OLMapWidget.js",
)

def map_outplantings_column_decorator(
        id: Union[str, int],
        outplantings: List[dict],
        size: int = 180,
):
    """
    changelist column code for showing Outplantings in a map

    :param id: some identifier to distinguish different maps. Used as JS identifier!
    :param outplantings: list of dict.
        required field is "location" of type geos.Point
    :param size: map width and height in pixels
    :return: html code
    """
    from geo.widgets import get_botgard_map_template_context
    from individuals.models.outplanting import Outplanting

    if not outplantings:
        return ""

    context = {
        **get_botgard_map_template_context(),
        "id": f"map-{id}",
        "name": id,
        "module": f"geodjango_{id}",
        "geom_type": "Point",
        "map_size": [size, size],
        "red_dots": True,
        "read_only": True,
        "outplantings": json.dumps(
            [
                {**obj, "location": f"SRID={Outplanting.location.field.srid};{obj['location'].wkt}"}
                for obj in outplantings
            ]
        ),
    }
    engine = Engine.get_default()
    return mark_safe(engine.render_to_string("geo/openlayers.html", context))


def map_feature_column_decorator(
        id: Union[str, int],
        features: List[geos.GEOSGeometry],
        size: int = 180,
        srid: int = 4326,
        default_zoom: Optional[float] = None,
):
    """
    changelist column code snippet for showing geo locations in a map

    :param id: some identifier to distinguish different maps. Used as JS identifier!
    :param features: list of geos.Geometry
    :param size: map width and height in pixels
    :param srid: projection
    :return: html code
    """
    from geo.widgets import get_botgard_map_template_context

    if not features:
        return ""

    context = {
        **get_botgard_map_template_context(
            default_zoom=default_zoom,
        ),
        "id": f"map-{id}",
        "name": id,
        "module": f"geodjango_{id}",
        "geom_type": "Point",
        "map_size": [size, size],
        "red_dots": True,
        "read_only": True,
        "features": json.dumps(list(
            f"SRID={srid};{feature.wkt}"
            for feature in features
        )),
    }
    engine = Engine.get_default()
    return mark_safe(engine.render_to_string("geo/openlayers.html", context))
