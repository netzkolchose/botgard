import time
import datetime

from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.template import Context, loader
from django.shortcuts import render
from django.apps import apps
from django.urls import reverse

from tools.permissions import *
from tools.admin_extensions import minimal_admin_context
from botman.models import *


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

    try:
        from_date = timezone.make_aware(from_date)
    except:
        pass
    try:
        to_date = timezone.make_aware(to_date)
    except:
        pass

    log_entries = list(
        LogEntry.objects.filter(
            action_time__gte=from_date,
            action_time__lte=to_date,
        ).order_by("-action_time", "object_repr")
    )
    existing_pks = {}
    for log in log_entries:
        key = log.content_type
        if key not in existing_pks:
            existing_pks[key] = [log.object_id]
        else:
            existing_pks[key].append(log.object_id)

    for content_type in existing_pks.keys():
        app_model = (content_type.app_label, content_type.model)
        try:
            existing_pks[content_type] = set(map(str,
                apps.get_model(*app_model).objects
                .filter(pk__in=existing_pks[content_type])
                .values_list("pk", flat=True)
            ))
        except Exception as e:
            print("X", type(e).__name__, e)
            existing_pks[content_type] = []

    log_entry_objects = []
    for log in log_entries:
        link = None
        if log.object_id in existing_pks[log.content_type]:
            link = reverse(
                "admin:{}_{}_change".format(log.content_type.app_label, log.content_type.model),
                args=(log.object_id, )
            )
        log_entry_objects.append({
            "action_time": log.action_time,
            "user": log.user,
            "content_type": str(log.content_type),
            "text": str(log),
            "link": link,
        })
    ctx = minimal_admin_context(request, LogEntry, _("user activity"))
    ctx.update({
        "from_date": from_date.date(),
        "to_date": to_date.date(),
        "log_entries": log_entry_objects,
        "histogram": histogram,
    })
    return render(request, "botman/activity.html", ctx)
