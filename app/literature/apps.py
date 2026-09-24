from django.utils.translation import gettext_lazy as _
from django.apps import AppConfig


class LiteratureConfig(AppConfig):
    name = 'literature'
    verbose_name = _("Literature")
