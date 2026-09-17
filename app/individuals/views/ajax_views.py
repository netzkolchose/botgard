import traceback

from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.shortcuts import render
from django.urls import reverse
from individuals.models import *
from tools.permissions import *
from individuals.numbers import generate_individual_ipen


@permission_required("individuals.view_individual")
def full_ipen_view(request):
    from botman.models import BotanicGarden

    pk = request.GET.get("pk")

    instance = Individual()
    instance.ipen_country = "xx"
    instance.ipen_transfer_restricted = "x"
    instance.ipen_garden_code = BotanicGarden(code="xxx")
    instance.ipen_accession_number = "x"

    if pk:
        try:
            instance = Individual.objects.get(pk=pk)
        except Individual.DoesNotExist:
            pass

    for key, value in request.GET.items():
        if key != "pk" and value:
            if key == "ipen_garden_code":
                instance.ipen_garden_code = BotanicGarden(code=value)
            else:
                setattr(instance, key, value)

    try:
        ipen = generate_individual_ipen(instance)
        return HttpResponse(ipen)
    except:
        traceback.print_exc()
        return HttpResponse(status=400)
