from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.shortcuts import render
from django.urls import reverse
from django.conf import settings
from individuals.models import *
from tools.permissions import *

import config_app
from tools.pdf import create_pdf_response
from tools.admin_extensions import minimal_admin_context
from individuals.models import Territory, Department


@login_required
def garden_map_view(request):
    ctx = minimal_admin_context(
        request, Territory,
        title=_("Garden map"),
        extra={
            "map_srid": 3857,
            "map_tile_url": settings.MAP_TILE_URL,
            "default_location": config_app.get_value("geo_location"),
            "territories": list(
                Territory.objects.all()
                .order_by("code")
                .values(
                    "pk", "code", "name",
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
        },
    )
    return render(request, 'individuals/garden_map.html', ctx)
