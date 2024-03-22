from django.utils.translation import gettext_lazy as _
from django.apps import AppConfig


class EntryBookConfig(AppConfig):
    name = 'entrybook'
    verbose_name = _("Seed / individual entry book")
