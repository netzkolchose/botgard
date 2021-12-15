from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ConfigAppConfig(AppConfig):
    name = 'config_app'
    verbose_name = _("Configuration")
