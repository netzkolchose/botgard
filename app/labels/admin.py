from django.contrib import admin
from django import forms
from django.template.loader import render_to_string

from .models import LabelDefinition


class SvgWidget(forms.Textarea):

    def render(self, name, value, attrs=None, renderer=None):
        context = {
            "widget": super(SvgWidget, self).render(name, value, attrs, renderer),
        }
        return render_to_string("labels/svg-widget.html", context)


class LabelDefinitionForm(forms.ModelForm):
    class Meta:
        widgets = {"svg_markup": SvgWidget}
    exclude = ()


class LabelDefinitionAdmin(admin.ModelAdmin):

    form = LabelDefinitionForm
    list_display = ("display_name", "id_name", "type", "preview_decorator")
    change_form_template = "labels/change_form.html"
    ordering = ("type", "display_name")

    class Media:
        js = (
            #"config_tables/jquery-3.1.1.min.js",
            "labels/codemirror/lib/codemirror.js",
            "labels/codemirror/mode/xml.js",
            "labels/change_form.js",
        )
        css = {"screen": ["labels/codemirror/lib/codemirror.css"]}

    def change_view(self, request, object_id, form_url='', extra_context=None):
        try:
            label = LabelDefinition.objects.get(pk=object_id)
            extra_context = extra_context or {}
            extra_context["svg_markup_plain"] = label.svg_markup
        except LabelDefinition.DoesNotExist:
            pass
        return super(LabelDefinitionAdmin, self).change_view(request, object_id, form_url, extra_context)


admin.site.register(LabelDefinition, LabelDefinitionAdmin)
