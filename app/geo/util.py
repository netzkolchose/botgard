from typing import Tuple

from django.utils.translation import gettext as _


def geo_coord_to_html(
        location: Tuple[float, float],
        digits: int = 6,
        digits_high: int = 8
) -> str:
    """
    Convert a geo-location to a html link on OSM

    6 digits after comma seems to be good enough for plants
    check: https://xkcd.com/2170/
    """
    location_high = (round(location[0], digits_high), round(location[1], digits_high))
    location_low = (round(location[0], digits), round(location[1], digits))
    osm_url = f"https://www.openstreetmap.org/#map=19/{location_high[1]}/{location_high[0]}"
    title = _("longitude: {}, latitude: {}").format(location_high[0], location_high[1])
    return f"""<a href="{osm_url}" target="_blank" title="{title}">{location_low[0]}/{location_low[1]}"""
