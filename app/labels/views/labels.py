import random

from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html

from labels.models import LabelDefinition, LABEL_FORMAT_TO_FILE_FORMAT
from individuals.models import Individual
from entrybook.models import Entry
from botman.models import BotanicGarden
from herbaria.models import HerbariumSpecimen
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
def label_entry(request, label_pk, entry_pk):
    """View to render entry book label"""
    return _render_label_entry(request, label_pk, entry_pk)


@login_required
def label_herbarium_specimen(request, label_pk, specimen_pk):
    """View to render specimen label"""
    return _render_herbarium_specimen_entry(request, label_pk, specimen_pk)


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
    if label.type == "entry":
        return label_random_entry(request, label_pk)
    if label.type == "herbarium_specimen":
        return label_random_herbarium_specimen(request, label_pk)

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


@login_required
def label_random_entry(request, label_pk):
    """View to render random entry label"""
    qset = Entry.objects.all()
    if not qset.exists():
        return HttpResponse(_("No entries defined"), status=404)

    entry = qset[random.randrange(qset.count())]

    return _render_label_entry(request, label_pk, entry.pk)


@login_required
def label_random_herbarium_specimen(request, label_pk):
    """View to render random herbarium specimen label"""
    qset = HerbariumSpecimen.objects.all()
    if not qset.exists():
        return HttpResponse(_("No entries defined"), status=404)

    model = qset[random.randrange(qset.count())]

    return _render_herbarium_specimen_entry(request, label_pk, model.pk)


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


def _render_label_entry(request, label_pk, entry_pk):
    """View implementation to render label for Entry"""
    try:
        label = LabelDefinition.objects.get(pk=label_pk)
    except LabelDefinition.DoesNotExist:
        return HttpResponse(_("Invalid label id"), status=404)

    if label.type != "entry":
        return HttpResponse(_("Invalid label type"), status=404)

    try:
        entry = Entry.objects.get(pk=entry_pk)
    except Entry.DoesNotExist:
        return HttpResponse(_("Invalid entry id"), status=404)

    context = label.get_entry_context(entry)

    return _render_impl(
        request, label, context,
        filename="%s" % (entry.ipen_generated or entry.accession_number),
        label_url=reverse("labels:entry", args=(label_pk, entry_pk))
    )


def _render_herbarium_specimen_entry(request, label_pk, specimen_pk):
    """View implementation to render label for HerbariumSpecimen"""
    try:
        label = LabelDefinition.objects.get(pk=label_pk)
    except LabelDefinition.DoesNotExist:
        return HttpResponse(_("Invalid label id"), status=404)

    if label.type != "herbarium_specimen":
        return HttpResponse(_("Invalid label type"), status=404)

    try:
        model = HerbariumSpecimen.objects.get(pk=specimen_pk)
    except HerbariumSpecimen.DoesNotExist:
        return HttpResponse(_("Invalid specimen id"), status=404)

    context = label.get_herbarium_specimen_context(model)

    return _render_impl(
        request, label, context,
        filename="%s" % model.individual.ipen_generated,
        label_url=reverse("labels:herbarium_specimen", args=(label_pk, specimen_pk))
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
        except KeyboardInterrupt:
            raise
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
        except KeyboardInterrupt:
            raise
        except Exception as e:
            import traceback
            return HttpResponse(
                format_html('<p class="error">{}: {} <pre>{}</pre></p>', type(e).__name__, e, traceback.format_exc())
            )
