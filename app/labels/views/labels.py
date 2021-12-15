import random

from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html

from labels.models import LabelDefinition, LABEL_FORMAT_TO_FILE_FORMAT
from individuals.models import Individual
from botman.models import BotanicGarden
from tools.permissions import login_required


@login_required
def label_garden(request, label_pk, garden_pk):
    """View to render garden address label"""
    return _render_label_garden(request, label_pk, garden_pk)


@login_required
def label_individual(request, label_pk, indi_pk):
    """View to render individual label"""
    return _render_label_individual(request, label_pk, indi_pk)


@login_required
def label_random(request, label_pk):
    """view to render a random label"""
    try:
        label = LabelDefinition.objects.get(pk=label_pk)
    except LabelDefinition.DoesNotExist:
        return HttpResponse(_("Invalid label id"), status=404)

    if label.type == "garden":
        return label_random_garden(request, label_pk)
    if label.type == "individual":
        return label_random_individual(request, label_pk)

    return HttpResponse(_("Invalid label type '%s'") % label.type, status=404)


@login_required
def label_random_individual(request, label_pk):
    """View to render random individual label"""
    qset = Individual.objects.all()
    if not qset.exists():
        return HttpResponse(_("No individuals"), status=404)

    indi = qset[random.randrange(qset.count())]

    return _render_label_individual(request, label_pk, indi.pk)


@login_required
def label_random_garden(request, label_pk):
    """View to render random garden address label"""
    qset = BotanicGarden.objects.all()
    if not qset.exists():
        return HttpResponse(_("No botanic gardens defined"), status=404)

    garden = qset[random.randrange(qset.count())]

    return _render_label_garden(request, label_pk, garden.pk)


def _render_label_individual(request, label_pk, indi_pk):
    """View implementation to render label for individual"""
    try:
        label = LabelDefinition.objects.get(pk=label_pk)
    except LabelDefinition.DoesNotExist:
        return HttpResponse(_("Invalid label id"), status=404)

    if label.type != "individual":
        return HttpResponse(_("Invalid label type"), status=404)

    try:
        indi = Individual.objects.get(pk=indi_pk)
    except Individual.DoesNotExist:
        return HttpResponse(_("Invalid individual id"), status=404)

    context = label.get_individual_context(indi)

    return _render_impl(
        request, label, context,
        "%s" % (indi.ipen_generated or indi.accession_number),
        reverse("labels:individual", args=(label_pk, indi_pk))
    )


def _render_label_garden(request, label_pk, garden_pk):
    """View implementation to render label for garden address"""
    try:
        label = LabelDefinition.objects.get(pk=label_pk)
    except LabelDefinition.DoesNotExist:
        return HttpResponse(_("Invalid label id"), status=404)

    if label.type != "garden":
        return HttpResponse(_("Invalid label type"), status=404)

    try:
        garden = BotanicGarden.objects.get(pk=garden_pk)
    except BotanicGarden.DoesNotExist:
        return HttpResponse(_("Invalid garden id"), status=404)

    context = label.get_garden_context(garden)

    return _render_impl(
        request, label, context,
        garden.name.replace(" ", "_"),
        reverse("labels:garden", args=(label_pk, garden_pk))
    )


def _render_impl(
        request,
        label: LabelDefinition,
        context: dict,
        filename: str = None,
        label_url: str = None,
):
    """Render implementation for label and template context"""
    format = request.GET.get("format", "html").lower()
    filename = request.GET.get("filename") or filename

    if format == "html":
        try:
            markup = label.render_markup(context)
        except BaseException as e:
            return HttpResponse('<p class="error">%s</p>' % e)

        # links to downloadable files
        if "include_links" in request.GET and label_url:
            links = []
            possible_formats = LABEL_FORMAT_TO_FILE_FORMAT[label.format]
            for fmt in possible_formats:
                links.append('<a href="%s?format=%s&filename=%s.%s">%s</a>' % (
                    label_url,
                    fmt,
                    filename, fmt,
                    fmt,
                ))
            markup += "<br>" + " • ".join(links)
        return HttpResponse(markup)

    else:
        try:
            return label.render_file_response(context, filename, format=format)
        except Exception as e:
            import traceback
            return HttpResponse(
                format_html('<p class="error">{}: {} <pre>{}</pre></p>', type(e).__name__, e, traceback.format_exc())
            )
