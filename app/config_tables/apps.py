from django.utils.translation import gettext_lazy as _
from django.apps import AppConfig


class ConfigTablesConfig(AppConfig):
    name = 'config_tables'
    verbose_name = _('Configuration of tables')