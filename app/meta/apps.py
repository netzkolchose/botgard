from django.utils.translation import gettext_lazy as _
from django.apps import AppConfig


class MetaConfig(AppConfig):
    name = 'meta'
    verbose_name = _("Meta")
