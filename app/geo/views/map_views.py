import json
import traceback

from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.shortcuts import render
from django.urls import reverse
from django.conf import settings
from django.db import transaction

import config_app
from tools.permissions import login_required
from tools.admin_extensions import minimal_admin_context
from individuals.models import Territory, Department


@login_required
def garden_map_view(request):

    has_write_permission = (
        request.user.has_perm("individuals.add_territory")
        or request.user.has_perm("individuals.change_territory")
        or request.user.has_perm("individuals.add_department")
        or request.user.has_perm("individuals.change_department")
    )
    has_read_permission = has_write_permission or (
        request.user.has_perm("individuals.view_territory")
        or request.user.has_perm("individuals.view_department")
    )

    context = minimal_admin_context(
        request, Territory,
        title=_("Garden map"),
    )

    if not has_read_permission:
        context["error"] = _("no permission")
    else:
        if request.method == "POST":
            if not has_write_permission:
                context["error"] = _("no write permission")
            else:
                try:
                    features = json.loads(request.POST.get("features"))["features"]
                    with transaction.atomic():
                        for feature in features:
                            model_class = Territory if feature["model"] == "territory" else Department
                            print(feature["wkt"])
                            model_class.objects.filter(pk=feature["pk"]).update(polygon=feature["wkt"])
                    context["info_message"] = _("The map has been saved")
                except:
                    traceback.print_exc()
                    context["error"] = _("Error reading form data")

        context.update({
            "map_srid": 3857,
            "map_tile_url": settings.MAP_TILE_URL,
            "default_location": config_app.get_value("geo_location"),
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

    return render(request, 'geo/garden_map.html', context)
