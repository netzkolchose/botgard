from django.utils.translation import gettext_lazy as _
from django.apps import AppConfig


class IndividualsConfig(AppConfig):
    name = 'individuals'
    verbose_name = _("Individuals and their locations")