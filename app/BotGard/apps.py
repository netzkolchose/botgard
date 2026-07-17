from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig
from django.utils.translation import gettext_lazy as _


class BotGardAppConfig(AppConfig):
    name = 'BotGard'
    verbose_name = _("BotGard")


class BotGardAdminConfig(AdminConfig):
    default_site = "BotGard.admin_site.BotGardAdminSite"
