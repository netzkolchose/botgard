import datetime
import random
import csv as csv_lib
from io import StringIO
from typing import Union, List, Tuple

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.template import Template, Context
from django.http import HttpResponse
from django.core.validators import RegexValidator
from django.utils.safestring import mark_safe
from django.utils.html import format_html


LABEL_TYPE_CHOICES = (
    ('garden', _("Botanic Garden")),
    ('individual', _("Individual")),
)

LABEL_ID_VALIDATOR = RegexValidator(
    r'^[0-9A-Za-z_]+$', _('Only alphanumeric characters and _ are allowed.'))

LABEL_FORMAT_CHOICES = (
    ('svg', _("SVG (Vector Graphics)")),
    ('csv', _("CSV (Table)")),
)

# Mapping of LabelDefinition.format to the possible file formats
LABEL_FORMAT_TO_FILE_FORMAT = {
    "svg": ["pdf", "png", "svg"],
    "csv": ["csv", "xls"],
}

FORMAT_CONTENT_TYPES = {
    "csv": "text/csv",
    "xls": "application/vnd.ms-excel",
    "pdf": "application/pdf",
    "png": "image/png",
    "svg": "application/svg",
    "zip": "application/zip",
}


class LabelDefinition(models.Model):
    class Meta:
        verbose_name = _("Label")
        verbose_name_plural = _("Labels")

    id_name = models.CharField(
        verbose_name=_("identification"), max_length=50, unique=True,
        validators=[LABEL_ID_VALIDATOR],
        help_text=_("This name is used to identify a label type in a label ticket. "
                    "You can replace a label by reusing it's identification name")
    )
    display_name = models.CharField(
        verbose_name=_("display name"),
        max_length=50,
    )
    type = models.CharField(
        verbose_name=_("label type"),
        max_length=30,
        choices=LABEL_TYPE_CHOICES,
        default='individual',
    )
    format = models.CharField(
        verbose_name=_("label format"),
        max_length=16,
        choices=LABEL_FORMAT_CHOICES,
        default="svg",
    )

    svg_markup = models.TextField(
        verbose_name=_("markup"),
    )

    def __str__(self):
        return self.display_name

    def preview_decorator(self):
        if self.type == "garden":
            from botman.models import BotanicGarden
            qset = BotanicGarden.objects.all()
            if not qset.exists():
                return ""
            return self.render_markup(self.get_garden_context(qset[random.randrange(qset.count())]))
        if self.type == "individual":
            from individuals.models import Individual
            qset = Individual.objects.all()
            if not qset.exists():
                return ""
            return mark_safe(self.render_markup(self.get_individual_context(qset[random.randrange(qset.count())])))
        return ""
    preview_decorator.short_description = _("preview")

    def render_markup(self, context):
        try:
            if self.format == "csv":
                row = self.render_csv_row(context)
                fp = StringIO()
                writer = csv_lib.writer(fp)
                writer.writerow(row)
                fp.seek(0)
                return fp.read().strip()
            else:
                before = '{% load i18n %}'
                t = Template(before + self.svg_markup)
                return t.render(Context(context))
        except Exception as e:
            return f"ERROR: {type(e).__name__}: {e}"

    def render(self, template_context: dict, format: str = "auto") -> Union[str, bytes]:
        from labels.svg_to_pdf import convert_svg_to_format
        from labels.csv_to_xls import convert_csv_to_xls

        if format == "auto":
            format = LABEL_FORMAT_TO_FILE_FORMAT[self.format][0]
        else:
            possible_file_formats = LABEL_FORMAT_TO_FILE_FORMAT[self.format]
            if format not in possible_file_formats:
                raise ValueError(f"Can not render a label of format '{self.format}' to format '{format}'")

        markup = self.render_markup(template_context)

        if self.format == "svg" and format != "svg":
            return convert_svg_to_format(markup, format)

        if self.format == "csv" and format == "xls":
            return convert_csv_to_xls(markup)

        return markup

    def render_csv_row(self, context: dict) -> List[str]:
        row = []
        template_lines = self.svg_markup.splitlines()
        for line in template_lines:
            before = '{% load i18n %}'
            t = Template(before + line)
            value = t.render(Context(context)).strip()
            row.append(value)
        return row

    def render_file(
            self,
            template_context: dict,
            filename: str = _("label.pdf"),
            format: str = "pdf",
    ) -> Tuple[str, str, Union[str, bytes]]:
        from labels import valid_filename

        filename = valid_filename(filename)

        if format == "auto":
            format = LABEL_FORMAT_TO_FILE_FORMAT[self.format][0]

        elif format not in FORMAT_CONTENT_TYPES:
            raise ValueError("Invalid format '%s', expected one of %s" % (format, ", ".join(FORMAT_CONTENT_TYPES)))

        if not filename.lower().endswith(f".{format}"):
            filename = filename + f".{format}"

        content = self.render(template_context, format)
        return filename, format, content

    def render_file_response(
            self,
            template_context: dict,
            filename: str = _("label.pdf"),
            format: str = "pdf",
    ) -> HttpResponse:
        filename, format, content = self.render_file(
            template_context=template_context, filename=filename, format=format,
        )
        response = HttpResponse(content, content_type=FORMAT_CONTENT_TYPES[format])
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename
        return response

    @classmethod
    def get_individual_context(cls, individual_or_pk):
        from individuals.models import Individual
        if isinstance(individual_or_pk, Individual):
            indi = individual_or_pk
        else:
            indi = Individual.objects.get(pk=individual_or_pk)
        context = _get_default_context()
        context["obj"] = indi
        return context

    @classmethod
    def get_garden_context(cls, garden_or_pk):
        from botman.models import BotanicGarden
        if isinstance(garden_or_pk, BotanicGarden):
            garden = garden_or_pk
        else:
            garden = BotanicGarden.objects.get(pk=garden_or_pk)
        context = _get_default_context()
        context["obj"] = garden
        return context


def _get_default_context():
    return {
        "today": datetime.date.today(),
    }

