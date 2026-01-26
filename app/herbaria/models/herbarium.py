from django.db import models, OperationalError
from django import forms
from django.forms import widgets
from django.forms.utils import ErrorList
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy as __
from django.urls import reverse
from django.templatetags.static import static
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
#from django.db.models.signals import post_save
#from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model

from config_tables.admin import configurable, Configurable


class Herbarium(Configurable, models.Model):

    class Meta:
        verbose_name = _("Herbarium")
        verbose_name_plural = _("Herbarium")

    _id_field = "name"

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=128,
        unique=True,
        db_index=True,
    )

    date_created = models.DateField(
        verbose_name=_("date created"),
        auto_now_add=True,
    )

    comment = models.TextField(
        verbose_name=_("Comment"),
        null=True, blank=True,
    )

    @configurable
    def __str__(self):
        return self.name

    __str__.admin_order_field = 'name'
    __str__.short_description = _('Herbarium')

    @configurable
    def change_link_decorator(self):
        return _("show")

    change_link_decorator.short_description = _("show")
    change_link_decorator.exclude_csv = True

    @configurable
    def delete_link_decorator(self):
        url = reverse("admin:herbaria_herbarium_delete", args=(self.pk,))
        return mark_safe('<a href="%s" class="deletelink">%s</a>' % (url, _("delete")))

    delete_link_decorator.short_description = _("delete")
    delete_link_decorator.exclude_csv = True
