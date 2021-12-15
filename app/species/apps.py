from django.apps import AppConfig
from django.utils.translation import ungettext_lazy as _


class SpeciesConfig(AppConfig):
    name = 'species'
    verbose_name = _('species', 'species', 2)
