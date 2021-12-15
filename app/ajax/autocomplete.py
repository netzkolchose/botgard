from typing import Optional

from django import forms
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.utils.translation import ugettext as _
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.urls import reverse


class AutoFieldMixin:
    """
    Lowlevel functionality for autocomplete forms/fields as Mixin.
    This handles lookups for fields of type text, text+choices and relation
    """
    def autofield_init(self, model_class, field_name):
        self.af_appname = model_class._meta.app_label
        self.af_model = model_class
        self.af_fieldname = field_name
        self.af_is_foreign = False
        self.af_is_choices = False
        field = self.af_model._meta.get_field(field_name)
        self.af_field = field

        # check foreign field
        if getattr(field, "related_model", None):
            self.af_model = field.related_model
            # TODO: all models essentially need '_id_field'
            # so that autocomplete has a valid unique identifier for ForeignKey models
            # currently there is this '_id_field' kludge applied to all relevant models
            # maybe there is a better solution!?
            self.af_fieldname = ""
            self.af_is_foreign = True
            if hasattr(self.af_model, "_id_field") and self.af_model._id_field:
                self.af_fieldname = self.af_model._id_field
            else:
                # use fallback
                # (fields that would identify a foreign model)
                for x in ["name", "username"]:
                    if hasattr(self.af_model, x):
                        self.af_fieldname = x
                        break
            if not self.af_fieldname:
                raise ValueError("model %s is not identified for foreign-key autocompletion" % self.af_model)

        elif hasattr(field, "choices") and field.choices:
            self.af_is_choices = True


    def autofield_widget_attrs(self, widget):
        meta = self.af_model._meta
        ret = {
            "class": "autocomplete-modelfield",
            "data-ac-json-url": reverse("ajax:choices_json") if self.af_is_choices else reverse("ajax:model_json"),
            "data-ac-id": "%s-%s-%s" % (meta.app_label, meta.model_name, self.af_fieldname),
        }
        if self.af_is_choices:
            ret["class"] += " autocomplete-choices autocomplete-verify"
        if self.af_is_foreign:
            ret["class"] += " autocomplete-relation autocomplete-verify"
        if self.af_is_choices or self.af_is_foreign:
            ret["placeholder"] = _("Type to search")
        return ret

    def autofield_prepare_value(self, value):
        if not self.af_is_foreign:
            if not self.af_is_choices:
                return value
            else:
                for c in self.af_field.choices:
                    if c[0] == value:
                        return c[1]
                return value
        try:
            id = int(value)
            o = self.af_model.objects.get(pk=id)
            return "%s" % o
        except (TypeError, ValueError, self.af_model.DoesNotExist):
            return value

    def _get_qset(self, value):
        filter = { "%s__exact" % self.af_fieldname: value}
        qset = self.af_model.objects.filter(**filter)
        if not qset.exists():
            filter = { "%s__icontains" % self.af_fieldname: value}
            qset = self.af_model.objects.filter(**filter)
        return qset

    def autofield_to_python(self, value):
        if not self.af_is_foreign:
            if not self.af_is_choices:
                return value
            else:
                for c in self.af_field.choices:
                    if value in c[1]:
                        return c[0]
                raise forms.ValidationError(
                    _('"%(value)s is not a valid choice for %(field)s') % {
                        "value": value, "field": "%s.%s" % (self.af_model._meta.verbose_name, self.af_fieldname)
                    }, code = "invalid")
        if not value:
            return None
        qset = self._get_qset(value)
        #print("to_python", filter, qset)
        if not qset.exists():
            raise forms.ValidationError(
                _('"%(value)s" is not an instance of the %(model)s model') % {
                    "value": value, "model": self.af_model._meta.verbose_name}, code='invalid')
        if qset.count() > 1:
            raise forms.ValidationError(
                _('"%(value)s" is not a unique identifier for the %(model)s model') % {
                    "value": value, "model": self.af_model._meta.verbose_name}, code='invalid')
        return qset[0]

    def autofield_queryset(self):
        qset = self.af_model.objects.all()
        return qset

    def autofield_get_instance(self, value):
        if not self.af_is_foreign:
            return None
        if not value:
            return None
        qset = self._get_qset(value)
        return qset[0] if qset.exists() and qset.count() == 1 else None


class AutoCharField(AutoFieldMixin, forms.CharField):
    """
    Classic text field with autocompletion.
    Also supports choices
    """
    def __init__(self, model_class, field_name, *args, **kwargs):
        self.autofield_init(model_class, field_name)
        super(AutoCharField, self).__init__(*args, **kwargs)
        if isinstance(self.widget, forms.Select):
            self.widget = forms.TextInput(self.widget_attrs(self.widget))

    def widget_attrs(self, widget):
        ret = super(AutoCharField, self).widget_attrs(widget)
        ret.update(self.autofield_widget_attrs(widget))
        return ret

    def prepare_value(self, value):
        value = super(AutoCharField, self).prepare_value(value)
        return self.autofield_prepare_value(value)

    def to_python(self, value):
        value = super(AutoCharField, self).to_python(value)
        return self.autofield_to_python(value)



class AutoModelWidget(forms.TextInput):
    """Form field for ForeignKey"""
    def __init__(self, attrs=None):
        if attrs is not None:
            self.af = attrs.pop("autocomplete")
        else:
            self.af = None
        super(AutoModelWidget, self).__init__(attrs)
        self.template = "ajax/autocomplete_related_widget.html"

    def get_related_url(self, info, action, *args):
        return reverse("admin:%s_%s_%s" % (info + (action,)),
                       current_app=self.af.af_appname, args=args)

    def render(self, name, value, *args, **kwargs):
        # print("RENDER", name, value, args, kwargs)
        rel_opts = self.af.af_model._meta
        info = (rel_opts.app_label, rel_opts.model_name)
        url_params = ""
        if 0:  # TODO: popup logic needs heavy js patching and everything
            from django.contrib.admin.views.main import IS_POPUP_VAR, TO_FIELD_VAR
            url_params = '&'.join("%s=%s" % param for param in [
                (TO_FIELD_VAR, name),
                (IS_POPUP_VAR, 1),
            ])
        # instance = self.af.autofield_get_instance(value)
        context = {
            'widget': super(AutoModelWidget, self).render(name, value, *args, **kwargs),
            'name': name,
            'url_params': url_params,
            'model': rel_opts.verbose_name,
            'url_change_related': self.get_related_url(info, 'change', '__fk__'),
            'url_add_related': self.get_related_url(info, 'add')
        }
        return mark_safe(render_to_string(self.template, context))


class AutoModelField(AutoCharField):
    def __init__(self, model_class, field_name, *args, **kwargs):
        super(AutoModelField, self).__init__(model_class, field_name, *args, **kwargs)
        self.widget = AutoModelWidget(self.widget_attrs(AutoModelWidget))

    def widget_attrs(self, widget):
        ret = super(AutoModelField, self).widget_attrs(widget)
        ret.update(autocomplete=self)
        return ret



def field_attrs(field):
    return {
        "required": field.required,
        "widget": field.widget,
        "label": field.label,
        "initial": field.initial,
        "help_text": field.help_text,
        "error_messages": field.error_messages,
        "show_hidden_initial": field.show_hidden_initial,
        "validators": field.validators,
        "localize": field.localize,
        "disabled": field.disabled,
        "label_suffix": field.label_suffix,
    }


def AutoCompleteForm(model_class, widgets: Optional[dict] = None):
    """
    Function to be used as Form class
    e.g.
    > class MyForm(AutoCompleteForm(MyModel)):
    >     pass
    """
    param_widgets = widgets

    class Form(forms.ModelForm):
        class Meta:
            model = model_class
            fields = '__all__'
            widgets = param_widgets

        class Media:
            js = (
                #'/static/config_tables/jquery-dollar.js',
                #'/static/config_tables/jquery-ui.min.js',
                '/static/ajax/autocomplete.js',
            )
            css = {
                "all": ('/static/ajax/autocomplete.css',),
            }

        def __init__(self, *args, **kwargs):
            super(Form, self).__init__(*args, **kwargs)
            for key in self.fields:
                if hasattr(self, "exclude_autocomplete"):
                    if key in self.exclude_autocomplete:
                        continue
                field = self.fields[key]
                attrs = field_attrs(field)
                if isinstance(field, forms.CharField):
                    self.fields[key] = AutoCharField(model_class, key, **attrs)
                elif isinstance(field, forms.ModelChoiceField):
                    self.fields[key] = AutoModelField(model_class, key, **attrs)
                elif isinstance(field, forms.ChoiceField) and len(field.choices) > 30:
                    self.fields[key] = AutoCharField(model_class, key, **attrs)

    return Form
