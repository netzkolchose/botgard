from django.utils.translation import gettext_lazy as _
from django.utils.html import mark_safe
from django.db import models


class KeyValue(models.Model):
    class Meta:
        verbose_name = _('Variable')
        verbose_name_plural = _('Variables')

    type = models.CharField(verbose_name=_('type'), max_length=1, default='t',
                            choices=(('t', _('translateable text')), ('j', _('json')))
                            )
    key = models.CharField(verbose_name=_('key'), max_length=255, unique=True, null=False, blank=False)

    value = models.TextField(verbose_name=_('value'), default="", blank=True)
    value_json = models.JSONField(verbose_name=_('json value'), null=True, blank=True)

    def clean(self):
        super(KeyValue, self).clean()
        from config_app import get_validator
        validator = get_validator(self.key)
        if validator:
            if self.type == 'j':
                validator(self.value_json)
            elif self.type == 't':
                validator(self.value)
            else:
                raise ValueError(_('Type unknown "%s"') % self.type)

    def description(self):
        from config_app import get_description
        try:
            return mark_safe(get_description(self.key))
        except KeyError:
            return None

    def __str__(self):
        return self.key

    def value_decorator(self):
        if self.type == 't':
            return self.value[:100]
        if self.type == 'j':
            ret = ("%s" % self.value_json)[:100]
            return ret.replace("{u'", "{'").replace("[u'", "['").replace(": u'", ": '").replace(", u'", ", '")
        raise ValueError(_('Invalid type in KeyValue "%s"') % self.type)
    value_decorator.short_description = _("value")
    value_decorator.admin_order_field = "value"
