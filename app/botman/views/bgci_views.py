import time
import datetime

from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.template import Context, loader
from django.shortcuts import render

from tools.permissions import *
from tools.admin_extensions import minimal_admin_context
from botman.models import *
from botman.utils import fuzzy_find_bgci_garden


MAP_BGCI_PERMISSION = ("botman.change_botanicgarden", "botman.view_bgcigarden")


@permission_required(*MAP_BGCI_PERMISSION)
def map_bgci_view(request: HttpRequest):

    num_per_page = 20
    page = 0

    garden_qset = BotanicGarden.objects.filter(bgci_id=None)
    garden_count = garden_qset.count()
    num_pages = garden_count // num_per_page

    gardens = list(
        garden_qset[page * num_per_page: (page + 1) * num_per_page]
        .values("pk", "name", "address")
    )
    bgci_gardens_per_garden = fuzzy_find_bgci_garden(
        *(f'{i["name"]} {i["address"]}'.strip() for i in gardens),
        max_num=10,
        with_scores=True,
    )

    def score_to_color(score: float, bgci_gardens):
        ma = 260 #bgci_gardens[0][1]
        mi = 200 #bgci_gardens[-1][1]
        return int(max(1., min(9., (score - mi) / max(0.00001, ma - mi) * 8 + 1)))

    def bgci_title(garden: BGCIGarden) -> str:
        fields = []
        for key in ("name", "address", "postal_code", "city", "state_or_province", "country"):
            if value := getattr(garden, key):
                fields.append(value)
        return "\n".join(fields)

    for garden, bgci_gardens in zip(gardens, bgci_gardens_per_garden):
        garden["bgci"] = [
            {
                "id": g.bgci_id,
                "name": f"{g.name}, {g.city.capitalize()}" if g.city and g.city.lower() not in g.name.lower() else g.name,
                "score": int(score),
                "title": bgci_title(g),
                "color": score_to_color(score, bgci_gardens),
            }
            for g, score in bgci_gardens
        ]
    ctx = minimal_admin_context(request, BotanicGarden, _("Map BGCI gardens"))
    ctx.update({
        "num_pages": num_pages,
        "gardens": gardens,
    })
    return render(request, "botman/map-bgci.html", ctx)


@permission_required(*MAP_BGCI_PERMISSION)
def assign_bgci_view(request: HttpRequest):
    try:
        garden_pk = int(request.GET.get("pk"))
        bgci_id = int(request.GET.get("id"))

        garden = BotanicGarden.objects.get(pk=garden_pk)
    except Exception as e:
        return HttpResponse(f"{type(e).__name__}: {e}", status=400)

    garden.bgci_id = bgci_id
    garden.save()

    return HttpResponse(status=201)
