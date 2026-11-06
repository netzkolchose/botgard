import random

from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html

from labels import valid_filename
from labels.models import LabelDefinition, LABEL_FORMAT_TO_FILE_FORMAT, LABEL_TYPE_TO_MODEL
from individuals.models import Individual
from entrybook.models import Entry
from botman.models import BotanicGarden
from herbaria.models import HerbariumSpecimen
from tools.permissions import login_required


@login_required
def label_garden(request, label_pk, garden_pk):
    """View to render garden address label"""
    return _render_label(request, label_pk, garden_pk)


@login_required
def label_entry(request, label_pk, entry_pk):
    """View to render entry book label"""
    return _render_label(request, label_pk, entry_pk)


@login_required
def label_individual(request, label_pk, indi_pk):
    """View to render individual label"""
    return _render_label(request, label_pk, indi_pk)


@login_required
def label_outplanting(request, label_pk, indi_pk):
    """View to render outplanting label"""
    return _render_label(request, label_pk, indi_pk)


@login_required
def label_herbarium_specimen(request, label_pk, specimen_pk):
    """View to render specimen label"""
    return _render_label(request, label_pk, specimen_pk)


@login_required
def label_random(request: HttpRequest, label_pk: int):
    """view to render a random label"""
    try:
        label = LabelDefinition.objects.get(pk=label_pk)
    except LabelDefinition.DoesNotExist:
        return HttpResponse(_("Invalid label id"), status=404)

    return globals()[f"label_random_{label.type}"](request, label_pk)


@login_required
def label_random_garden(request, label_pk):
    """View to render random garden address label"""
    return _label_random_type(request, label_pk, "garden")


@login_required
def label_random_entry(request, label_pk):
    """View to render random entry label"""
    return _label_random_type(request, label_pk, "entry")


@login_required
def label_random_individual(request: HttpRequest, label_pk: int):
    """View to render random individual label"""
    return _label_random_type(request, label_pk, "individual")


@login_required
def label_random_outplanting(request, label_pk):
    """View to render random outplanting label"""
    return _label_random_type(request, label_pk, "outplanting")


@login_required
def label_random_herbarium_specimen(request, label_pk):
    """View to render random herbarium specimen label"""
    return _label_random_type(request, label_pk, "herbarium_specimen")


def _label_random_type(request: HttpRequest, label_pk: int, type: str):
    """
    Implementation for random label view
    """
    qset = LABEL_TYPE_TO_MODEL[type].objects.all()
    if not qset.exists():
        return HttpResponse(f"No {type}", status=404)

    pk = qset.values_list("pk", flat=True)[random.randrange(qset.count())]

    return _render_label(request, label_pk, pk)



def _render_label(request: HttpRequest, label_pk: int, instance_pk: int):
    """
    View implementation to render label for a specific model instance
    """
    try:
        label = LabelDefinition.objects.get(pk=label_pk)
    except LabelDefinition.DoesNotExist:
        return HttpResponse(_("Invalid label id"), status=404)

    try:
        instance = label.model_class.objects.get(pk=instance_pk)
    except Individual.DoesNotExist:
        return HttpResponse(_("Invalid model id"), status=404)

    context, filename = label.get_model_context(instance, return_filename=True)

    return _render_impl(
        request=request,
        label=label,
        context=context,
        filename=filename,
        label_url=reverse("labels:individual", args=(label_pk, instance_pk))
    )


def _render_impl(
        request,
        label: LabelDefinition,
        context: dict,
        filename: str = None,
        label_url: str = None,
):
    from labels import valid_filename

    """Render implementation for label and template context"""
    format = request.GET.get("format", "html").lower()
    filename = valid_filename(request.GET.get("filename") or filename)

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
