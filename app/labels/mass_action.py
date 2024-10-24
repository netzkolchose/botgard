import traceback
from functools import partial
import csv as csv_lib
from io import StringIO, BytesIO
import zipfile
from typing import List, Union, Tuple

from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
from django.contrib.admin import ModelAdmin
from django.contrib import messages
from django.template import Template, Context
from django.utils.safestring import mark_safe

from labels.csv_to_xls import convert_csv_to_xls
from .models import (
    LabelDefinition,
    LABEL_TYPE_CHOICES,
    FORMAT_CONTENT_TYPES,
    LABEL_FORMAT_TO_FILE_FORMAT,
)
from botman.models import BotanicGarden
from individuals.models import Individual, Seed
from entrybook.models import Entry
from tools.pdf import render_html_to_pdf


def add_label_mass_actions(request, actions: dict, label_type: str):
    from labels.models import LabelDefinition

    labels_qset = LabelDefinition.objects.filter(type=label_type).order_by("display_name")
    for pk, id_name, display_name, format in labels_qset.values_list(
            "pk", "id_name", "display_name", "format"
    ):

        if format not in ("csv", "html"):
            action_name = f"label_{id_name}"
            actions[action_name] = (
                partial(render_mass_labels_action, label_pk=pk),
                action_name,
                _("Label: %(name)s") % {"name": display_name}
            )

        else:
            formats = ("csv", "xls") if format == "csv" else ("pdf", "html")
            for format in formats:
                action_name = f"label_{id_name}_{format}"
                actions[action_name] = (
                    partial(render_mass_labels_action, label_pk=pk, format=format),
                    action_name,
                    _("Label: %(name)s (%(format)s)") % {"name": display_name, "format": format.upper()}
                )

    return actions


def render_mass_labels_action(admin: ModelAdmin, request, queryset, label_pk, format: str = "auto"):
    try:
        pks = list(queryset.values_list("pk", flat=True))
        if not pks:
            admin.message_user(
                request,
                _("No objects have been selected"),
                level=messages.ERROR,
            )
            return

        label = LabelDefinition.objects.get(pk=label_pk)

        file_format, content = render_mass_labels(label, pks, format=format)

        response = HttpResponse(content, content_type=FORMAT_CONTENT_TYPES[file_format])
        if file_format != "html":
            response['Content-Disposition'] = 'attachment; filename="%s.%s"' % (
                _("labels"), file_format
            )
        return response

    except Exception as e:
        admin.message_user(
            request,
            _("Error creating labels: %s") % f"{type(e).__name__}: {e} | {traceback.format_exc()}",
            level=messages.ERROR,
        )


def render_mass_labels(
        label: LabelDefinition,
        pks: List[int],
        format: str = "auto"
    ) -> Tuple[str, Union[str, bytes]]:
    """
    Renders all labels, returns tuple of (file-format, content)
    """
    if label.format == "csv":
        ret_format = "csv"
        if format == "xls":
            ret_format = "xls"
        return ret_format, _render_mass_labels_csv(label, pks, format)

    elif label.format == "svg":
        if len(pks) >= 2:
            return "zip", _render_mass_labels_svg(label, pks, format)
        else:
            return _render_single_label_svg(label, pks[0], format)

    elif label.format == "html":
        if format == "auto":
            format = "html"
        return format, _render_mass_labels_html(label, pks, format)
    else:
        raise AssertionError(f"Invalid format '{label.format}' on label '{label.id_name}'")


def _render_mass_labels_csv(label: LabelDefinition, pks: List[int], format: str = "auto") -> Union[str, bytes]:
    """
    Renders all labels and returns CSV (string) or excel (binary) data
    """
    rows = []
    for pk in pks:
        context = getattr(label, f"get_{label.type}_context")(pk)

        if not rows:
            header_row = label.render_csv_row(context, header=True)
            rows.append(header_row)

        row = label.render_csv_row(context)
        rows.append(row)

    if format in ("auto", "csv"):
        fp = StringIO()
        writer = csv_lib.writer(fp)
        writer.writerows(rows)
        fp.seek(0)
        return fp.read().strip()

    elif format == "xls":
        return convert_csv_to_xls(rows)

    else:
        raise ValueError("Invalid format '%s', expected one of %s" % (format, ", ".join(LABEL_FORMAT_TO_FILE_FORMAT["csv"])))


def _render_mass_labels_svg(label: LabelDefinition, pks: List[int], format: str = "auto") -> bytes:
    """
    Renders all labels and returns zip file data
    """
    zip_file_io = BytesIO()
    with zipfile.ZipFile(zip_file_io, "w") as zip_file:
        for pk in pks:
            context = getattr(label, f"get_{label.type}_context")(pk)

            filename = str(pk)
            if label.type == "individual":
                filename = Individual.objects.get(pk=pk).id_name_generated
            elif label.type == "garden":
                filename = BotanicGarden.objects.get(pk=pk).full_name_generated
            elif label.type == "entry":
                filename = Entry.objects.get(pk=pk).id_name_generated

            filename, real_format, content = label.render_file(context, filename, format)
            zip_file.writestr(filename, content)

    zip_file_io.seek(0)
    return zip_file_io.read()


def _render_single_label_svg(label: LabelDefinition, pk: int, format: str = "auto"):
    """
    Renders all labels and returns zip file data
    """
    context = getattr(label, f"get_{label.type}_context")(pk)

    filename = str(pk)
    if label.type == "individual":
        filename = Individual.objects.get(pk=pk).id_name_generated
    elif label.type == "garden":
        filename = BotanicGarden.objects.get(pk=pk).full_name_generated
    elif label.type == "entry":
        filename = Entry.objects.get(pk=pk).id_name_generated

    filename, real_format, content = label.render_file(context, filename, format)
    return real_format, content


def _render_mass_labels_html(label: LabelDefinition, pks: List[int], format: str = "auto") -> Union[str, bytes]:
    """
    Renders all labels and returns HTML or PDF file data
    """
    markups_per_object = []

    for pk in pks:
        context = getattr(label, f"get_{label.type}_context")(pk)

        markup = label.render_markup(context, without_page_markup=True)
        markups_per_object.append(markup)

    if not label.page_markup or not label.page_markup.strip():
        final_markup = "\n".join(markups_per_object)

    else:
        context = {"content": mark_safe("\n".join(markups_per_object))}
        final_markup = Template(label.page_markup).render(Context(context))

    if format in ("auto", "html"):
        return final_markup

    elif format == "pdf":
        return render_html_to_pdf(final_markup)

