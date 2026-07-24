from django.contrib import admin

from django.contrib import admin
from django.contrib import admin
from django.forms import ModelForm, HiddenInput
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import django.contrib.gis.forms as gis_forms
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline

from .models import *
from geo.widgets import BotGardOpenLayersWidget


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
        fields = ['type', 'key', 'value', 'value_normal_text', 'value_json', 'value_geo']

    value_geo = gis_forms.PointField(
        srid=KeyValue.value_geo.field.srid,
        widget=BotGardOpenLayersWidget(),
    )

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
                if instance.type != "j":
                    self.disable_field("value_json")
                if instance.type != "t":
                    self.disable_field("value")
                    for lang, lang_name in settings.LANGUAGES:
                        self.disable_field("value_%s" % lang)
                if instance.type != "n":
                    self.disable_field("value_normal_text")
                if instance.type != "g":
                    self.disable_field("value_geo")

    def disable_field(self, name):
        if name in self.fields:
            self.fields[name].widget = HiddenInput()
            self.fields[name].required = False

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



class CustomPropertyAdmin(admin.ModelAdmin):
    list_display = (
        'change_link_decorator',
        'model', 'name', 'type_decorator', 'required', 'order', 'times_used_decorator', 'date_created',
    )
    search_fields = ('name', )

    fieldsets = (
        (None, {"fields": (
            "model",
            ("name", "order"),
            ("type", "required"),
            "choices",
        )}),
    )

    list_filter = ("model", )
    list_editable = ("order", "required")

    def type_decorator(self, instance: CustomProperty):
        type = instance.type
        for key, label in CUSTOM_PROPERTY_TYPE_CHOICES:
            if type == key:
                type = label
                break
        if ch := instance.get_choices():
            type = _("Text ({} choices)").format(len(ch))
        return type
    type_decorator.short_description = _("type")
    type_decorator.admin_order_field = "type"

    def times_used_decorator(self, instance: CustomProperty):
        if instance.type == "bool":
            return instance.values_bool.count()
        else:
            return instance.values_text.count()
    times_used_decorator.short_description = _("# used")


admin.site.register(CustomProperty, CustomPropertyAdmin)


if 0:  # just for debugging, take a look at the actual values

    class PropertyValueBoolAdmin(admin.ModelAdmin):
        list_display = ('property__model', 'property__name', 'value')
        search_fields = ('propery__name', )

    admin.site.register(PropertyValueBool, PropertyValueBoolAdmin)


    class PropertyValueTextAdmin(admin.ModelAdmin):
        list_display = ('property__model', 'property__name', 'value')
        search_fields = ('propery__name', 'value')

    admin.site.register(PropertyValueText, PropertyValueTextAdmin)
