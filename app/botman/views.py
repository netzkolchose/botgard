import time
import datetime

from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.template import Context, loader
from django.shortcuts import render

from tools.permissions import *

from .models import *

from tools.admin_extensions import minimal_admin_context


# TODO: cleanup

@login_required
def index_page(request):
    return HttpResponseRedirect("/admin/")


# default fallback for "write_permission_required" decorators
def no_permission_page(request):
    return HttpResponse('<p>%s</p><p><a href="/admin/logout/">%s</a></p>'
                        % (_("Sorry, but you do not have write permission!"),
                           _("Log out and change user")))


@admin_required
def data_admin_view(request):

    from individuals.models import Individual
    ctx = minimal_admin_context(request, Individual, "data administration")

    from config_tables.models import TableSettings
    ctx["table_settings"] = TableSettings.objects.all()

    if request.method == "POST":
        from tools.data_migration import (
            calc_all, calc_outplantings, calc_individuals_outplantings,
            assign_territory, strip_whitespace
        )

        ctx["info"] = ", ".join("%s" % k for k in request.POST.keys() if k != "csrfmiddlewaretoken")
        start_time = time.time()

        if "recalc-all" in request.POST:
            calc_all()

        elif "recalc-individuals-outplantings" in request.POST:
            calc_individuals_outplantings()

        elif "recalc-outplanting" in request.POST:
            calc_outplantings()

        elif "assign-territory" in request.POST:
            assign_territory()

        elif "strip-whitespace" in request.POST:
            strip_whitespace()

        elif "del-table-settings" in request.POST:
            try:
                pk = int(request.POST.get("pk", 0))
                ts = TableSettings.objects.get(pk=pk)
                ts.delete()
                ctx["info"] = _("Deleted <b>%s</b>" % ts)
            except (ValueError, TypeError, TableSettings.DoesNotExist):
                ctx["error"] = _("Invalid id")

        took = time.time() - start_time
        ctx["info"] = "<p><b>%s</b></p><p>took %s sec</p>" % (ctx.get("info", ""), round(took, 2))

    return render(request, "botman/data-admin.html", ctx)


@admin_required
def activity_view(request):

    from django.contrib.admin.models import LogEntry

    to_date = timezone.now()
    from_date = to_date - timezone.timedelta(days=7)
    if "dt" in request.GET:
        from_date = timezone.datetime.fromordinal(int(request.GET["dt"]))
        to_date = from_date + timezone.timedelta(days=7)

    log_entries = LogEntry.objects.all().order_by("-action_time")
    action_times = [t[0] for t in log_entries.values_list("action_time")]
    histogram = dict()
    for t in action_times:
        bin = t.toordinal() // 7
        histogram[bin] = histogram.get(bin, 0) + 1
    max_hist = max(histogram.values()) if histogram else 1
    histogram = [("%s" % round(histogram[bin]*100./max_hist, 2),
                  histogram[bin],
                  datetime.date.fromordinal(bin*7),
                  bin*7,
                  ) for bin in sorted(histogram)]

    log_entries = LogEntry.objects.filter(action_time__gte=from_date,
                                          action_time__lte=to_date).order_by("-action_time")

    ctx = minimal_admin_context(request, LogEntry, _("user activity"))
    ctx.update({
        "from_date": from_date.date(),
        "to_date": to_date.date(),
        "log_entries": log_entries,
        "histogram": histogram,
    })
    return render(request, "botman/activity.html", ctx)
