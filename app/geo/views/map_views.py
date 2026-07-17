import json
import traceback

from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.shortcuts import render
from django.urls import reverse
from django.db import transaction
from django.core.serializers.json import DjangoJSONEncoder

from tools.permissions import login_required
from tools.admin_extensions import minimal_admin_context
from individuals.models import Territory, Department


@login_required
def garden_map_view(request):
    from geo.widgets import get_botgard_map_template_context

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
    response_status = 200

    if not has_read_permission:
        context["error"] = _("no permission")
        response_status = 403
    else:
        context.update({
            "has_write_permission": has_write_permission,
            **get_botgard_map_template_context(),
        })

    return render(request, 'geo/garden_map.html', context, status=response_status)


@login_required
def garden_map_json_view(request):

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

    response = {
        "status": 200,
    }

    if not has_read_permission:
        response["error"] = _("no permission")
        response["status"] = 403
    else:
        if request.method == "POST":
            if not has_write_permission:
                response["error"] = _("no write permission")
                response["status"] = 403
            else:
                try:
                    features = json.loads(request.body)["features"]
                    with transaction.atomic():
                        for feature in features:
                            model_class = Territory if feature["model"] == "territory" else Department
                            model_class.objects.filter(pk=feature["pk"]).update(polygon=feature["wkt"])
                    response["message"] = _("The map has been saved")
                    response["status"] = 202
                except:
                    traceback.print_exc()
                    response["error"] = _("Error reading form data")

    return HttpResponse(json.dumps(response, cls=DjangoJSONEncoder), status=response["status"])
