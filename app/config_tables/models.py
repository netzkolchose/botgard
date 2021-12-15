from django.db import models
from picklefield.fields import PickledObjectField
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User


class TableSettings(models.Model):
    class Meta:
        verbose_name = _('table settings')
        verbose_name_plural = _('tables settings')
        unique_together = ('user', 'model')
    user = models.ForeignKey(User, verbose_name=_('user'), related_name='tablesettings', on_delete=models.CASCADE)
    model = models.CharField(verbose_name=_('model'), max_length=255)
    settings = PickledObjectField(editable=True)

    def __str__(self):
        return '%s - %s' % (self.model, self.user)
