from typing import Union, Optional

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe


def get_label_choices(label_class):
    """Returns a list of tuples with (id_name, display_name) for the given label class"""
    from .models import LabelDefinition
    qset = LabelDefinition.objects.filter(type=label_class)
    if not qset.exists():
        return None
    return tuple((l.id_name, l.display_name) for l in qset)


def valid_filename(filename: str) -> str:
    """
    Strips all non-ascii or special characters from the filename
    and replaces spaces with underscores.
    :param filename: str
    :return: str
    """
    filename = filename.replace(" ", "_")
    filename = filename.encode("utf-8").decode("ascii", errors="ignore")
    filename = "".join(
        c for c in filename
        if c.isalnum() or c in ("-", "_", ".")
    )
    return filename


def label_link_decorator(
        label_class: str,
        object_pk: Union[str, int],
        filename: Optional[str] = None,
        format: str = "auto",
):
    """
    Creates a link or a select field to a handler that returns label file responses.

    :param label_class: str
        - "individual" maps to individuals.models.Individual
        - "address" maps to botman.models.BotanicGarden

    :param object_pk: str|int
        - primary key of the individual / seed / botanic garden

    :param filename: str, optional
        The filename of the http response attachment.
        If the file extension does not match the specified format,
        it is automatically added.

        Spaces are replaced with underscores and only ASCII
        characters are included.

    :param format: str
        - "auto": choose the first format in `LABEL_FORMAT_TO_FILE_FORMAT`
        - "pdf", "png", "csv", ...: force specific format
            Note that it must match the mapping in `LABEL_FORMAT_TO_FILE_FORMAT`

    :return: html markup
    """
    from .models import LabelDefinition, LABEL_FORMAT_TO_FILE_FORMAT
    from django.template.loader import render_to_string

    qset = LabelDefinition.objects.filter(type=label_class)
    if not qset.exists():
        return mark_safe('<a href="%s?type=%s">%s</a>!' % (
            reverse("admin:labels_labeldefinition_add"),
            label_class,
            _("define a label first"),
        ))

    filename = valid_filename(filename or _("label"))

    # only single label defined?
    if qset.count() == 1:
        return mark_safe('<a href="%s?filename=%s&format=%s">%s</a>' % (
            reverse("labels:%s" % label_class, args=(qset[0].pk, object_pk)),
            filename,
            format,
            format,
        ))

    labels = list(qset)
    labels.sort(key=lambda l: l.display_name)

    c_labels = []

    for label in labels:
        c_labels.append(
            {
                "url": "%s?filename=%s&format=%s" % (
                    reverse("labels:%s" % label_class, args=(label.pk, object_pk)),
                    filename,
                    format
                ),
                "name": label.display_name,
                "title": "",
            }
        )

    context = {
        "title": _('select label'),
        "items": c_labels
    }

    return render_to_string('BotGard/css_dropdown/css_dropdown.html', context)
