from django.utils.translation import gettext_lazy as _
from django.apps import AppConfig


class SeedcatalogConfig(AppConfig):
    name = 'seedcatalog'
    verbose_name = _("Seed catalogs")