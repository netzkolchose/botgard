from django.utils.translation import gettext_lazy as _

from django.db import models
from django.contrib.auth.models import (User, Group)
from django_extensions.db.models import TimeStampedModel


class SideBarLinkMeta(models.Model):
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)

    url = models.CharField(_('URL'), max_length=4096, blank=False)
    title = models.CharField(_('title'), max_length=255, blank=False)
    order = models.IntegerField(_('order'), default=0, blank=False)

    def __str__(self):
        return '%s (%s) [%s]'%(self.title, self.url, self.user)

    class Meta:
        abstract = True


class BookMark(SideBarLinkMeta):
    pass


class Note(TimeStampedModel):
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)

    url = models.CharField(_('URL'), max_length=4096, blank=False)
    note = models.TextField(_('note'), max_length=4096, blank=True)

    public = models.BooleanField(_('public'), default=False, null=False)
