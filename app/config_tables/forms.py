from django.forms import ModelForm, Field, ValidationError
from .models import TableSettings
from django.template import loader, Context
from json import dumps, loads
from django.forms.widgets import TextInput
from django.utils.translation import ugettext as _
from django.core.serializers.json import DjangoJSONEncoder


# TODO: test in form.save, if user is allowed to alter user/model

# load template only once at startup
TEMPLATE = loader.get_template('config_tables/tablesettings_widget.html')


class TableSettingsWidget(TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        c = {
            'instance': self.instance,
            'opts': self.extra_opts,
            'selected': self.selected,
            'settings_id': attrs.get('id')
        }
        attrs.update({'type': 'hidden'})
        return super(TextInput, self).render(name, value, attrs, renderer) + TEMPLATE.render(c)


class TableSettingsField(Field):
    widget = TableSettingsWidget

    def to_python(self, value):
        return loads(value)


class TableSettingsForm(ModelForm):
    class Media:
        css = {'all': ('config_tables/config_tables.css',)}
        js = (#'/static/admin/js/vendor/jquery/jquery.js',
              #'/static/admin/js/jquery.init.js',
              #'/static/config_tables/jquery-dollar.js',
              #'config_tables/jquery-3.1.1.min.js',
              'config_tables/jquery-ui.min.js',
              'config_tables/jquery-sortable.js',
              'config_tables/config_tables.js')

    class Meta:
        model = TableSettings
        fields = ['user', 'model', 'settings']

    settings = TableSettingsField(required=False)

    def __init__(self, *args, **kwargs):
        extra_opts = kwargs.get('extra_opts')
        if extra_opts:
            del kwargs['extra_opts']
        selected = kwargs.get('selected')
        if 'selected' in kwargs:
            del kwargs['selected']
        super(TableSettingsForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance')
        if instance:
            self.fields['user'].widget.attrs['disabled'] = True
            self.fields['user'].widget.attrs['disabled'] = True
            self.fields['model'].widget.attrs['disabled'] = True
            self.fields['settings'].widget.instance = instance
        self.fields['settings'].widget.extra_opts = extra_opts
        #if selected:
        #    self.fields['settings'].widget.selected = selected
        #    self.fields['settings'].initial = dumps(selected)
        self.fields['settings'].widget.selected = selected
        self.fields['settings'].initial = dumps(selected, cls=DjangoJSONEncoder)

    def clean_settings(self):
        data = self.cleaned_data['settings']
        if not data:
            raise ValidationError(_('At least one field should be selected. Form was reset to previous selection.'))
        return next(zip(*data))

    def reset_selection(self, selected):
        self.fields['settings'].widget.selected = selected
        self.fields['settings'].initial = dumps(selected)
