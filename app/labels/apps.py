from django.apps import AppConfig

from django.utils.translation import gettext_lazy as _


class LabelsConfig(AppConfig):
    name = 'labels'
    verbose_name = _("Labels")
