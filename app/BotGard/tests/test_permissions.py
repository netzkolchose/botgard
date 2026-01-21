import pprint
from typing import Dict, Set


from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.admindocs.views import simplify_regex
from django.utils import timezone
from django.contrib.auth import get_user_model

import bs4

from individuals.models import Seed
from seedcatalog.models import SeedCatalog

from botman.management.commands.botgard_demo_data import add_demo_data
from .fixtures import create_test_fixtures


class TestPermissions(TestCase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def test_permissions_admin(self):
        self.assertTrue(
            self.client.login(username="User1", password="the-secret"),
            "failed to log in"
        )
        self.assert_admin_permissions({
            'auth.group': {'add', 'change'},
            'auth.user': {'add', 'change'},
            'botman.bgcigarden': {'add', 'change'},
            'botman.botanicgarden': {'add', 'change'},
            'botman.externalcatalog': {'add', 'change'},
            'botman.externalcatalogarchive': {'add', 'change'},
            'botman.outgoingorder': {'add', 'change'},
            'entrybook.entry': {'add', 'change'},
            'individuals.department': {'add', 'change'},
            'individuals.individual': {'add', 'change'},
            'individuals.outplanting': {'add', 'change'},
            'individuals.seed': {'add', 'change'},
            'individuals.territory': {'add', 'change'},
            'labels.labeldefinition': {'add', 'change'},
            'seedcatalog.seedcatalog': {'add', 'change'},
            'species.family': {'add', 'change'},
            'species.species': {'add', 'change'},
            'tickets.basicticket': {'add', 'change'},
            'tickets.lasergravurticket': {'add', 'change'},
            'tickets.myticket': {'add', 'change'}
        })

    def test_permissions_guest(self):
        self.assertTrue(
            self.client.login(username="User2", password="the-secret"),
            "failed to log in"
        )
        self.assert_admin_permissions({})

    def assert_admin_permissions(self, expected_permissions: Dict[str, Set[str]]):
        permissions = self.get_admin_permissions()
        self.assertEqual(
            expected_permissions,
            permissions,
            f"\nExpected:\n{pprint.pformat(expected_permissions)}\nGot:\n{pprint.pformat(permissions)}",
        )

    def get_admin_permissions(self):
        response = self.client.get(reverse("admin:index"))
        soup = bs4.BeautifulSoup(response.content.decode(), features="html.parser")

        gathered_permissions = {}
        for group_div in soup.find_all("div", {"class": "module"}):

            app_name = None
            if cls := group_div.attrs.get("class"):
                if cls[0].startswith("app-"):
                    app_name = cls[0][4:]

            if app_name:
                for tr in group_div.find_all("tr"):

                    if cls := tr.attrs.get("class"):
                        if cls[0].startswith("model-"):
                            model_name = cls[0][6:]
                            perms = set()
                            if list(tr.find_all("a", {"class": "changelink"})):
                                perms.add("change")
                            if list(tr.find_all("a", {"class": "addlink"})):
                                perms.add("add")

                            gathered_permissions[f"{app_name}.{model_name}"] = perms

        return gathered_permissions
