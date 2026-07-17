from pathlib import Path
import requests

from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.shortcuts import render
from django.urls import reverse
from django.conf import settings


def raster_tile_cached_view(request: HttpRequest, zoom: int, x: int, y: int):
    """
    Some little caching view for OSM raster tiles.

    Only used for `./manage.py runserver` local deployment to avoid nginx proxy requirement.
    Caches the tiles in MEDIA_ROOT / "_tile_cache"

    """
    tile_path = f"{zoom}/{x}/{y}.png"
    local_tile_path: Path = settings.MEDIA_ROOT / "_tile_cache" / tile_path

    content = None
    if not local_tile_path.exists():
        response = requests.get(
            url=f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png",
            headers={
                "user-agent": "https://netzkolchose.de (BotGard)",
            }
        )
        if response.status_code != 200:
            return HttpResponse(status=response.status_code)

        local_tile_path.parent.mkdir(parents=True, exist_ok=True)
        local_tile_path.write_bytes(response.content)
        content = response.content

    if content is None:
        content = local_tile_path.read_bytes()

    return HttpResponse(
        content,
        headers={
            "content-type": "image/png",
        }
    )