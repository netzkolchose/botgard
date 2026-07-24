import copy
import pprint

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.urls import reverse


class BotGardAdminSite(admin.AdminSite):
    """
    Override normal AdminSite to
    - conveniently add extra links to admin app lists

    """
    def extra_app_links(self) -> list:
        """
        Add extra app links here!
        """
        return [
            {
                "app": "individuals",
                "name": _("Garden map"),
                "url": reverse("geo:garden_map"),
            },
        ]

    def _build_app_dict(self, request, label=None) -> dict:
        dic = super()._build_app_dict(request, label)

        for link in self.extra_app_links():
            if link["app"] in dic:
                dic[link["app"]]["models"].append({
                    "model": None,
                    "admin_url": link["url"],
                    'name': link["name"],
                    'add_url': None,
                })

        return dic
