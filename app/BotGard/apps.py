from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig
from django.utils.translation import gettext_lazy as _


class BotGardAppConfig(AppConfig):
    name = 'BotGard'
    verbose_name = _("BotGard")

    def ready(self):
        from config_app.basemodel import check_custom_property_classes
        check_custom_property_classes()


class BotGardAdminConfig(AdminConfig):
    default_site = "BotGard.admin_site.BotGardAdminSite"
