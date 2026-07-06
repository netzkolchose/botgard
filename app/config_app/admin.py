from django.contrib import admin

from django.contrib import admin
from .models import (KeyValue)

from modeltranslation.admin import TranslationAdmin, TranslationTabularInline

from django.contrib import admin
from django.forms import ModelForm, HiddenInput
from django.utils.translation import gettext_lazy as _
from django.conf import settings


# Helper for translations
class TabbedTranslationAdmin(TranslationAdmin):
    pass

    class Media:
        js = (
            'modeltranslation/js/force_jquery.js',
            'config_tables/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',

        )
        css = {
            'screen': (
                'modeltranslation/css/tabbed_translation_fields.css',
            ),
        }
# /Helper


class KeyValueForm(ModelForm):
    class Meta:
        model = KeyValue
        fields = ['type', 'key', 'value', 'value_normal_text', 'value_json']

    def __init__(self, *args, **kwargs):
        super(KeyValueForm, self).__init__(*args, **kwargs)

        self._disabled_fields = set()
        instance = getattr(self, 'instance')
        if instance:
            # on-the-fly settings for form-widgets depending on user-created vs. _defaults
            from config_app import _defaults
            if instance.key in _defaults:
                # can only change key or type of user-created
                self.disable_field("key")
                self.disable_field("type")
                # disable specific fields
                if instance.type in ("t", "n"):
                    self.disable_field("value_json")
                if instance.type in ("j", "n"):
                    self.disable_field("value")
                    for lang, lang_name in settings.LANGUAGES:
                        self.disable_field("value_%s" % lang)
                if instance.type in ("t", "j"):
                    self.disable_field("value_normal_text")

    def disable_field(self, name):
        if name in self.fields:
            self.fields[name].widget = HiddenInput()

    def clean(self):
        "Need to ignore errors related to disabled fields because django assumes their values to be unset otherwise"
        super(KeyValueForm, self).clean()
        for name in self._disabled_fields:
            if name in self._errors:
                del self._errors[name]
        return self.cleaned_data


class KeyValueAdmin(TabbedTranslationAdmin):
    list_display = ('key', 'type', 'value_decorator', 'description')
    search_fields = ('key', 'value', )
    change_form_template = "config_app/change_form.html"
    form = KeyValueForm

    def get_model_perms(self, *args, **kwargs):
        perms = admin.ModelAdmin.get_model_perms(self, *args, **kwargs)
        perms['index_list_hide'] = True
        return perms


admin.site.register(KeyValue, KeyValueAdmin)
