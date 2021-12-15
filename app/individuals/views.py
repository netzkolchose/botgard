from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.shortcuts import render
from django.urls import reverse
from individuals.models import *
from tools.permissions import *

# from tools.countries import get_iso_country_by_id
from tools.pdf import create_pdf_response
from tools.admin_extensions import minimal_admin_context
from tools.csv_response import csv_response


def unescape(x):
    return x.replace("&nbsp;", " ").replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')\
        .replace('&quot;', '"').replace('&#39;', "'")


def _table_row(row):
    WIDTHS = (50, 80, 0, 80, 80, 200)
    markup = "".join(
                '<td %s align="%s">%s</td>' % (
                    'width="%spx"' % WIDTHS[i] if WIDTHS[i] else "",
                    'center' if WIDTHS[i] else 'left',
                    c)
                for i, c in enumerate(row)
            )
    return '<tr>%s</tr>' % markup


def _checklist_view(request, Model, forId, outplantings_list):
    """
    Unified individuals checklist view for Departments and Territories
    :param request: Django request object
    :param Model: Department | Territory
    :param forId: pk of Department or Territory
    :param outplantings_list: Django QuerySet of corresponsing Outplantings
    :return: HttpResponse
    """

    outplantings_list = outplantings_list.order_by(
        "individual__species__family__family",
        "individual__species__family__genus",
        "individual__species__species",
    )

    result_len = outplantings_list.count()

    if Model is Department:
        department = Model.objects.get(id=forId)
        territory = department.territory
        instance = department
        location_name = "%(terr)s-%(dep)s (%(code)s)" % {
            "terr": territory.name,
            "dep": department.name,
            "code": department.code,
        }
        location_code = department.code
    else:
        department = None
        territory = Model.objects.get(id=forId)
        instance = territory
        location_name = "%(terr)s (%(code)s)" % {
            "terr": territory.name,
            "code": territory.code,
        }
        location_code = territory.code

    # simplified CSV response
    if "csv" in request.GET:
        headers = (
            _("Department"),
            _("Nr."),
            _("Species"),
            _("Planted"),
            _("Died?"),
        )
        rows = [("%s" % o.department.full_code,
                 "%s" % o.individual.accession_number + (("-%s" % o.individual.accession_extension) if o.individual.accession_extension else ""),
                 "%s %s" % (o.individual.species.family.family, o.individual.species.full_name()),
                 "%s" % o.date if o.date else "",
                 "%s" % o.plant_died if o.plant_died else "",
                ) for o in outplantings_list]
        import re
        code_part = re.sub(r" |_|\(|\)", "-", location_code)
        return csv_response("%s-%s.csv" % (Model._meta.verbose_name, code_part), headers, rows)

    headers = _table_row(["", _("Nr."), _("Species"), _("Planted"), _("Died?"), _("Comment")])
    rows = []
    for i, outpl in enumerate(outplantings_list):
        rows.append(_table_row([
            outpl.department.full_code,
            "%s" % outpl.individual.accession_number + (("-%s" % outpl.individual.accession_extension) if outpl.individual.accession_extension else ""),
            '<a href="%s">%s</a>' % (
                reverse("admin:individuals_individual_change", args=(outpl.individual.pk,)),
                '%s %s' %(outpl.individual.species.family.family, outpl.individual.species.full_name())
            ),
            "%s" % outpl.date if outpl.date else "",
            '<div class="checkbox %s"></div>' % ("checkbox_checked" if outpl.plant_died else ""),
            '',
        ]))

    ctx = minimal_admin_context(request, Model,
        title=_("Inventory list") + " %s - %s" % (location_name, timezone.now().date()),
        extra={
            "headers": headers,
            "rows": "\n".join(rows),
            'territory': instance,
            'result_len': result_len,
        }
    )
    return render(request, 'individuals/checklist.html', ctx)


@login_required
def checklist_territory(request, forId):
    qset = Outplanting.objects.filter(department__territory=forId)
    qset = qset.filter(plant_died=None) | qset.filter(individual__seed_available=True)

    return _checklist_view(request, Territory, forId, qset)


@login_required
def checklist_department(request, forId):
    qset = Outplanting.objects.filter(department=forId)
    qset = qset.filter(plant_died=None) | qset.filter(individual__seed_available=True)

    return _checklist_view(request, Department, forId, qset)


@login_required
def generate_label(request, individualId, labelId):
    try:
        indi = Individual.objects.get(pk=individualId)
    except:
        return HttpResponse(_("Individual %s not found") % str(individualId), status=400)
    try:
        label = label_types.get_label_for_id(int(labelId))
    except:
        # return HttpResponse(_("Label type %s unknown<br/>%s") % (str(labelId), str(ALL_LABEL_TYPES)), status=400)
        return HttpResponse(_("Label type %s unknown") % str(labelId), status=400)

    if not indi.species.nomenclature_checked:
        return HttpResponse("<h2>%s</h2><h3>%s</h3><p>%s</p>" % (
            _("Label can not be printed."),
            _("Nomenclature has not been verified."),
            _("Please ask your <i>Kustos</i>")
        ))

    # TODO: check if IPEN always gives valid filename
    filename = "%s-%s.pdf" % (str(indi.ipen_generated), label[label_types.IDX_ID])
    response = create_pdf_response(filename)

    try:
        render_label(response, indi, label)
        return response
    except:
        return HttpResponse(_("Label creation failed, sorry"), status=500)


