import re
import pprint
import secrets
import webbrowser
import itertools
from pathlib import Path
import tempfile
from typing import Dict, Set, Optional, Type

from django.test import TestCase, Client
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.db import models
from django.utils import timezone
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, Group
from django.contrib.auth import get_user_model

import bs4

from botman.models import *
from entrybook.models import *
from species.models import *
from individuals.models import *
from labels.models import *
from tickets.models import *
from seedcatalog.models import *

from .fixtures import create_permission_group, create_test_fixtures
from config_app.management.commands.botgard_update_config import update_config_in_database


GARDENER_PERMISSIONS = {
    'botman.bgcigarden': {'add', 'change'},
    'botman.botanicgarden': {'add', 'change'},
    'botman.externalcatalog': {'view'},
    'botman.externalcatalogarchive': {'view'},
    'botman.outgoingorder': {'add', 'change', 'delete'},
    'entrybook.entry': {'add', 'change', 'delete'},
    'individuals.department': {'add', 'change'},
    'individuals.individual': {'add', 'change'},
    'individuals.outplanting': {'add', 'change'},
    'individuals.seed': {'add', 'change'},
    'individuals.territory': {'add', 'change'},
    'labels.labeldefinition': {'view'},
    'seedcatalog.seedcatalog': {'view'},
    'species.family': {'add', 'change'},
    'species.species': {'add', 'change'},
    'tickets.basicticket': {'add', 'change', 'delete'},
    'tickets.lasergravurticket': {'add', 'change'},
    'tickets.myticket': {'add', 'change', 'delete'}
}

class TestPermissions(TestCase):
    PW = "the-secret"

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()
        update_config_in_database()

        cls.ALL_MODELS = {}
        for app_name, models in apps.all_models.items():
            for model_name, model in models.items():
                # filter for models that are visible as changelist/changeview
                if f"{app_name}.{model_name}" not in (
                        "admin.logentry",
                        "sessions.session",
                        "auth.permission",
                        "auth.user_groups",
                        "auth.user_user_permissions",
                        "auth.group_permissions",
                        "contenttypes.contenttype",
                        "easy_thumbnails.source",
                        "easy_thumbnails.thumbnail",
                        "easy_thumbnails.thumbnaildimensions",
                        "config_tables.tablesettings",
                        "sidebar.bookmark",
                        "sidebar.note",
                        "tickets.etikett_individual",
                        "seedcatalog.seedcatalog_seed",
                        "plantimages.plantimage",
                ):
                    cls.ALL_MODELS[f"{app_name}.{model_name}"] = model

        get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password=cls.PW,
        )
        user = get_user_model().objects.create_user(
            username="gardener",
            email="gardener@example.com",
            password=cls.PW,
            is_staff=True,
        )
        group = create_permission_group(
            "gardeners",
            GARDENER_PERMISSIONS,
        )
        user.groups.add(group)

        BasicTicket.objects.create(
            created_by=User.objects.get(username="User1"),
            directed_to=user, due_date="2100-01-01", title="Ticket for gardener",
        )
        user = get_user_model().objects.create_user(
            username="noaccess",
            email="noaccess@example.com",
            password=cls.PW,
            is_staff=True,  # staff user without any permissions
        )
        #print(group)
        #print(user.groups.all())
        #for perm in Group.objects.get(name="gardeners").permissions.all():
        #    print(perm)
        #    print(perm.codename, perm.content_type.app_label, perm.content_type.model)

    def show_html(self, html: str):
        fn = Path(tempfile.tempdir) / f"botgard-test-{secrets.token_hex(10)}.html"
        fn.write_text(html)
        webbrowser.open(f"file://{fn}")

    def login(self, username: str):
        self.assertTrue(
            self.client.login(username=username, password=self.PW),
            "failed to log in"
        )
        self.current_user = username

    def test_permissions_admin(self):
        self.login("admin")
        self.assert_staff_permissions({
            'auth.group': {'add', 'change'},
            'auth.user': {'add', 'change'},
            'botman.bgcigarden': {'add', 'change'},
            'botman.botanicgarden': {'add', 'change'},
            'botman.externalcatalog': {'add', 'change'},
            'botman.externalcatalogarchive': {'add', 'change'},
            'botman.outgoingorder': {'add', 'change'},
            'entrybook.entry': {'add', 'change'},
            'herbaria.herbarium': {'add', 'change'},
            'herbaria.herbariumspecimen': {'add', 'change'},
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

    def test_permissions_noaccess(self):
        self.login("noaccess")
        self.assert_staff_permissions({})

    def test_permissions_gardener(self):
        self.login("gardener")
        self.assert_staff_permissions({
            'botman.bgcigarden': {'add', 'change'},
            'botman.botanicgarden': {'add', 'change'},
            'botman.externalcatalog': {'change'},
            'botman.externalcatalogarchive': {'change'},
            'botman.outgoingorder': {'add', 'change'},
            'entrybook.entry': {'add', 'change'},
            'individuals.department': {'add', 'change'},
            'individuals.individual': {'add', 'change'},
            'individuals.outplanting': {'add', 'change'},
            'individuals.seed': {'add', 'change'},
            'individuals.territory': {'add', 'change'},
            'labels.labeldefinition': {'change'},
            'seedcatalog.seedcatalog': {'change'},
            'species.family': {'add', 'change'},
            'species.species': {'add', 'change'},
            'tickets.basicticket': {'add', 'change'},
            'tickets.lasergravurticket': {'add', 'change'},
            'tickets.myticket': {'add', 'change'}
        })

    def test_gardener(self):
        self.login("gardener")
        self.assert_models_access(
            can_change_models=[
                BGCIGarden, BotanicGarden, OutgoingOrder,
                Species, Family,
                Entry, Department, Territory, Individual, Seed, Outplanting,
                BasicTicket, LaserGravurTicket, MyTicket
            ],
            can_view_models=[
                ExternalCatalog, ExternalCatalogArchive,
                LabelDefinition, SeedCatalog, BasicTicket, LaserGravurTicket, MyTicket
            ]
        )

    def assert_models_access(
            self,
            can_change_models: List[Type[models.Model]],
            can_view_models: List[Type[models.Model]],
    ):
        """Assert that all model classes are viewable/changeable and remaining classes are not"""
        all_models = set(self.ALL_MODELS.values())
        view_models = set(can_view_models) | set(can_change_models)
        not_view_models = all_models - view_models
        change_models = set(can_change_models)
        not_change_models = all_models - change_models

        for model_class in view_models:
            self.assert_model_changelist(model_class)
            model = self.get_model_for_user(model_class, self.current_user)
            self.assert_model_changeview(
                model_class, model.pk,
                expect_read_access=True,
                expect_write_access=model_class in change_models,
            )

        for model_class in not_view_models:
            self.assert_model_changelist(model_class, expect_no_access=True)
            model = self.get_model_for_user(model_class, self.current_user)
            self.assert_model_changeview(model_class, model.pk, expect_read_access=False, expect_write_access=False)

        for model_class in change_models:
            self.assert_model_changelist(model_class)
            model = self.get_model_for_user(model_class, self.current_user)
            self.assert_model_changeview(model_class, model.pk, expect_read_access=True, expect_write_access=True)

        for model_class in not_change_models:
            model = self.get_model_for_user(model_class, self.current_user)
            self.assert_model_changeview(
                model_class, model.pk,
                expect_read_access=model_class in view_models,
                expect_write_access=False,
            )

    def get_model_for_user(self, model_class: Type[models.Model], username: str):
        qset = model_class.objects.all()
        if issubclass(model_class, MyTicket):
            count = qset.count()
            qset = qset.filter(directed_to__username=username)
            if count and not qset.count():
                raise NotImplementedError(f"Missing MyTicket for user {username}")

        model = qset.first()
        if not model:
            raise NotImplementedError(
                f"Missing model fixture for {model_class} (user {username})"
                ", add it to BotGard/tests/fixtures.py"
            )
        return model

    def test_garden(self):
        self.run_test_model(
            BotanicGarden,
            {
                "number": 666,
                "name": "GardenXY"
            },
        )

    def run_test_model(self, model_class: Type[models.Model], data: dict):
        self.client.logout()
        self.create_model(model_class, {}, expect_no_access=True)
        self.login("noaccess")
        self.create_model(model_class, {}, expect_no_access=True)

        self.login("admin")
        pk = self.create_model(model_class, data)

    def assert_model_changelist(
            self,
            model_class: Type[models.Model],
            expect_no_access: bool = False,
    ):
        app_name = model_class._meta.app_label
        model_name = model_class._meta.model_name
        url = reverse(f"admin:{app_name}_{model_name}_changelist")
        self.get_response(url, expect_no_access=expect_no_access)

    def assert_model_changeview(
            self,
            model_class: Type[models.Model],
            pk: int,
            expect_read_access: bool = True,
            expect_write_access: bool = True,
    ):
        app_name = model_class._meta.app_label
        model_name = model_class._meta.model_name
        url = reverse(f"admin:{app_name}_{model_name}_change", args=(pk,))
        self.get_response(url, expect_no_access=not (expect_read_access or expect_write_access))
        self.change_model(model_class, pk, expect_no_access=not expect_read_access, expect_no_write_access=not expect_write_access)

    def get_response(
            self,
            url: str,
            expect_no_access: bool = False,
            msg: str = "",
    ):
        if msg:
            msg = f", {msg}"

        response = self.client.get(url)
        if expect_no_access:
            if (not (
                    (response.status_code == 302 and "/admin/login/" in response.headers.get("Location", ""))
                    or response.status_code == 403
            )):
                raise AssertionError(f"Expected 302 or 403, got status {response.status_code} for url {url}{msg}")
            return response
        else:
            if response.status_code != 200:
              raise AssertionError(f"Expected 200, got {response.status_code} for url {url}{msg}")
        return response

    def create_model(
            self,
            model_class: Type[models.Model],
            data: dict,
            expect_no_access: bool = False,
    ) -> Optional[int]:
        """
        Create a new model entry in admin view

        :param model_class: django Model class
        :param data: dict, fields to enter
        :param expect_no_access: bool, If True, expected redirect to login
        :return: primary key of model
        """
        app_name = model_class._meta.app_label
        model_name = model_class._meta.model_name

        if not expect_no_access:
            # make sure it's listed in the admin:index
            perms = self.get_staff_permissions()
            self.assertIn(
                f"{app_name}.{model_name}",
                perms
            )

        url = reverse(f"admin:{app_name}_{model_name}_add")
        response = self.get_response(url, expect_no_access=expect_no_access)
        if expect_no_access:
            return

        soup = bs4.BeautifulSoup(response.content, features="html.parser")
        form = soup.find("form", {"id": f"{model_name}_form"})

        post_data = {}
        for inp in form.find_all("input"):
            name = inp.attrs["name"]
            if name in data:
                post_data[name] = data[name]
            elif "value" in inp.attrs:
                post_data[name] = inp.attrs["value"]

        post_data["_continue"] = "Save and continue editing"
        response = self.client.post(url, post_data)
        if response.status_code != 302:
            raise AssertionError(f"Creation failed for {url}, status={response.status_code}")

        change_url = response.headers["Location"]
        match = re.match(f".*admin/{app_name}/{model_name}/(\\d+)/change/", change_url)
        if not match:
            raise AssertionError(f"Got wrong redirect url {change_url}")
        return int(match.groups()[0])

    def change_model(
            self,
            model_class: Type[models.Model],
            pk: int,
            expect_no_access: bool = False,
            expect_no_write_access: bool = False,
            msg: str = "",
    ) -> Optional[int]:
        """
        Load changeview for model and POST form as is

        :param model_class: django Model class
        :param pk: int, model's primary key
        :param expect_no_access: bool, If True, expected redirect to login
        :return: primary key of model
        """
        if msg:
            msg = f", {msg}"
        else:
            msg = ""
        msg = f", expect_no_access={expect_no_access}, expect_no_write_access={expect_no_write_access}{msg}"

        app_name = model_class._meta.app_label
        model_name = model_class._meta.model_name
        model_instance = model_class.objects.get(pk=pk)

        if not expect_no_access:
            # make sure it's listed in the admin:index
            perms = self.get_staff_permissions()
            self.assertIn(
                f"{app_name}.{model_name}",
                perms
            )

        url = reverse(f"admin:{app_name}_{model_name}_change", args=(pk, ))
        response = self.get_response(url, expect_no_access=expect_no_access, msg=msg)
        if response.status_code in (302, 403):
            return

        soup = bs4.BeautifulSoup(response.content, features="html.parser")
        form = soup.find("form", {"id": f"{model_name}_form"})

        post_data = {}
        for inp in form.find_all("input"):
            if "value" in inp.attrs and inp.attrs["type"] != "submit":
                post_data[inp.attrs["name"]] = inp.attrs["value"]
        for inp in form.find_all("textarea"):
            if inp.text:
                post_data[inp.attrs["name"]] = inp.text
        for inp in form.find_all("select"):
            val = None
            for opt in inp.find_all("option"):
                if value := opt.attrs.get("value"):
                    if "selected" in opt.attrs:
                        val = value
                        break
            if val is not None:
                post_data[inp.attrs["name"]] = val

        for field in model_instance._meta.fields:
            if field.name not in post_data:
                post_data[field.name] = getattr(model_instance, field.name) or ''

        post_data["_continue"] = "Save and continue editing"
        response = self.client.post(url, post_data)
        if expect_no_write_access:
            if response.status_code != 403:
                raise AssertionError(f"Expected 403 for {url}, status={response.status_code}{msg}")
            return
        if response.status_code != 302:
            self.show_html(response.content.decode())
            raise AssertionError(f"Changing failed for {url}, status={response.status_code}{msg}")

        change_url = response.headers["Location"]
        match = re.match(f".*admin/{app_name}/{model_name}/{pk}/change/", change_url)
        if not match:
            raise AssertionError(f"Got wrong redirect url {change_url}{msg}")

    def assert_staff_permissions(self, expected_permissions: Dict[str, Set[str]]):
        permissions = self.get_staff_permissions()
        self.assertEqual(
            expected_permissions,
            permissions,
            f"\nExpected:\n{pprint.pformat(expected_permissions)}\nGot:\n{pprint.pformat(permissions)}",
        )

    def get_staff_permissions(self):
        """
        Get the list of permissions (visible models scraped from the admin index view)
        """
        response = self.client.get(reverse("admin:index"))
        if response.status_code != 200:
            raise AssertionError("No access to admin:index")
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
