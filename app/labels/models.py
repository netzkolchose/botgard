import datetime
import random
import csv as csv_lib
from io import StringIO
from typing import Union, List, Tuple

from asgiref.typing import HTTPResponseBodyEvent
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
    ('entry', _("Entry")),
    ('herbarium_specimen', _("Specimen")),
)

LABEL_ID_VALIDATOR = RegexValidator(
    r'^[0-9A-Za-z_]+$', _('Only alphanumeric characters and _ are allowed.'))

LABEL_FORMAT_CHOICES = (
    ('svg', _("SVG (Vector Graphics)")),
    ('csv', _("CSV (Table)")),
    ('html', _("HTML (Page)")),
)

# Mapping of LabelDefinition.format to the possible file formats
# first file format is default (when using format="auto")
LABEL_FORMAT_TO_FILE_FORMAT = {
    "svg": ["pdf", "png", "svg"],
    "csv": ["csv", "xls"],
    "html": ["pdf", "html"],
}

FORMAT_CONTENT_TYPES = {
    "csv": "text/csv",
    "html": "text/html",
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

    markup = models.TextField(
        verbose_name=_("markup"),
        help_text=_("The template for SVG, CSV or HTML"),
    )

    page_markup = models.TextField(
        verbose_name=_("page markup"),
        help_text=_("The outer template for HTML. The rendered markup from above is available as {{content}}"),
        null=True, blank=True,
    )

    def __str__(self):
        return self.display_name

    def preview_decorator(self):
        if self.type == "garden":
            from botman.models import BotanicGarden
            qset = BotanicGarden.objects.all()
            if not qset.exists():
                return ""
            markup = self.render_markup(self.get_garden_context(qset[random.randrange(qset.count())]))
        elif self.type == "individual":
            from individuals.models import Individual
            qset = Individual.objects.all()
            if not qset.exists():
                return ""
            markup = self.render_markup(self.get_individual_context(qset[random.randrange(qset.count())]))
        elif self.type == "herbarium_specimen":
            from herbaria.models import HerbariumSpecimen
            qset = HerbariumSpecimen.objects.all()
            if not qset.exists():
                return ""
            markup = self.render_markup(self.get_herbarium_specimen_context(qset[random.randrange(qset.count())]))
        else:
            return ""
        markup = f"""<div class="label-preview-background">{markup}</div>"""
        return mark_safe(markup)

    preview_decorator.short_description = _("preview")

    def render_markup(self, context: dict, without_page_markup: bool = False) -> str:
        """
        Render the label's markup template using the template context.

        :param context: dict, provided context
        :param without_page_markup: bool, for label of format `html`, only render using `markup` and without `page_markup`
        :return: rendered markup string
        """
        try:
            if self.format == "csv":
                header_row = self.render_csv_row(context, header=True)
                row = self.render_csv_row(context)
                fp = StringIO()
                writer = csv_lib.writer(fp)
                writer.writerow(header_row)
                writer.writerow(row)
                fp.seek(0)
                return fp.read().strip()
            else:
                t = Template(f"{{% load i18n %}}{self.markup}")
                markup = t.render(Context(context))

                if not self.format == "html" or not self.page_markup or not self.page_markup.strip():
                    return markup
                else:
                    t = Template(f"{{% load i18n %}}{self.page_markup}")
                    return t.render(Context({"content": mark_safe(markup)}))

        except Exception as e:
            return f"ERROR: {type(e).__name__}: {e}"

    def render(self, template_context: dict, format: str = "auto") -> Union[str, bytes]:
        """
        Renders the label in desired format, returns str/bytes
        """
        from labels.svg_to_pdf import convert_svg_to_format
        from labels.csv_to_xls import convert_csv_to_xls
        from tools.pdf import render_html_to_pdf

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

        if self.format == "html" and format == "pdf":
            return render_html_to_pdf(markup)

        return markup

    def render_csv_row(self, context: dict, header: bool = False) -> List[str]:
        """
        Render a single row of CSV data.

        :param context: dict, the template context
        :param header: bool, if True, render the header fields, if False render the content
        :return: list of str
        """
        row = []
        template_lines = self.markup.splitlines()
        if header:
            template_lines = template_lines[::2]
        else:
            template_lines = template_lines[1::2]

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
        """
        Calls `self.render()` and returns
            - adjusted filename
            - output format (in case format was "auto")
            - content (html, pdf bytes, etc...)
        """
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
        if format == "auto":
            format = LABEL_FORMAT_TO_FILE_FORMAT[self.format][0]

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

    @classmethod
    def get_entry_context(cls, entry_or_pk):
        from entrybook.models import Entry
        if isinstance(entry_or_pk, Entry):
            indi = entry_or_pk
        else:
            indi = Entry.objects.get(pk=entry_or_pk)
        context = _get_default_context()
        context["obj"] = indi
        return context

    @classmethod
    def get_herbarium_specimen_context(cls, specimen_or_pk):
        from herbaria.models import HerbariumSpecimen
        if isinstance(specimen_or_pk, HerbariumSpecimen):
            model = specimen_or_pk
        else:
            model = HerbariumSpecimen.objects.get(pk=specimen_or_pk)
        context = _get_default_context()
        context["obj"] = model
        return context


def _get_default_context():
    return {
        "today": datetime.date.today(),
    }

