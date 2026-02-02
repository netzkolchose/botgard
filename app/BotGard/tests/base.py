import re
import io
import csv
import pprint
import zipfile
import secrets
import webbrowser
import itertools
import subprocess
from pathlib import Path
import tempfile
from typing import Dict, Set, Optional, Type, Callable

from django.test import TestCase, Client
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.db import models
from django.utils import timezone
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, Group
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse, QueryDict

import bs4
import xlrd

from botman.models import *
from entrybook.models import *
from species.models import *
from individuals.models import *
from labels.models import *
from tickets.models import *
from seedcatalog.models import *
from herbaria.models import *

from .fixtures import create_permission_group, create_test_fixtures
from config_app.management.commands.botgard_update_config import update_config_in_database


class TestBase(TestCase):

    def login(self, username: str, password: str = "the-secret"):
        self.assertTrue(
            self.client.login(username=username, password="the-secret"),
            f"failed to log in {username}"
        )

    def get_form_data(self, form: bs4.PageElement) -> dict:
        data = {}

        def _add_data(key: str, value):
            if key not in data:
                data[key] = value
            else:
                if not isinstance(data[key], list):
                    data[key] = [data[key]]
                data[key].append(value)

        for inp in form.find_all("input"):
            if "value" in inp.attrs and inp.attrs["type"] != "submit":
                _add_data(inp.attrs["name"], inp.attrs["value"])

        for inp in form.find_all("textarea"):
            if inp.text:
                _add_data(inp.attrs["name"], inp.text)

        for inp in form.find_all("select"):
            val = None
            for opt in inp.find_all("option"):
                if value := opt.attrs.get("value"):
                    if "selected" in opt.attrs:
                        val = value
                        break
            if val is not None:
                _add_data(inp.attrs["name"], val)

        return data

    def show_html(self, html_or_response: Union[str, HttpResponse]):
        """Debugging method to open an html page in the browser"""
        if isinstance(html_or_response, HttpResponse):
            html = html_or_response.content.decode()
        elif isinstance(html_or_response, str):
            html = html_or_response
        else:
            raise TypeError(f"Expected str or HttpResponse, got {type(html_or_response).__name__}")

        fn = Path(tempfile.tempdir) / f"botgard-test-{secrets.token_hex(10)}.html"
        fn.write_text(html)
        webbrowser.open(f"file://{fn}")

    def assert_no_warning(self, response: HttpResponse):
        for pattern in (
                b'li class="warning"',
                b'p class="error"',
        ):
            if pattern in response.content:
                idx = response.content.index(pattern)
                snippet = response.content[idx: idx + 200]
                raise AssertionError(f"warning/error found in response {response}: {snippet}")

    def get_label_response(
            self,
            label_model: LabelDefinition,
            object_type: str,
            object_model: Union[models.Model, List[models.Model]],
            format: str,
            expect_unchecked_nomenclature: bool = False,
    ):
        if isinstance(object_model, list):
            if object_type == "garden":
                url = reverse("admin:botman_botanicgarden_changelist")
            elif object_type == "herbarium_specimen":
                url = reverse("admin:herbaria_herbariumspecimen_changelist")
            elif object_type == "individual":
                url = reverse("admin:individuals_individual_changelist")
            else:
                raise NotImplementedError(f"object_type '{object_type}' not implemented")

            action_name = f"label_{label_model.id_name}"
            if format != "pdf":
                if format == "true_pdf":
                    format = "pdf"
                action_name = f"label_{label_model.id_name}_{format}"

            response = self.client.post(
                url,
                data={
                    "action": action_name,
                    "_selected_action": [str(o.pk) for o in object_model],
                },
                follow=True,
            )
            #self.show_html(response)

            # handle confirmation page for unchecked nomenclatures of species
            if expect_unchecked_nomenclature:
                if b"have no validated nomenclature" not in response.content:
                    raise AssertionError(
                        f"Expected mass-label confirmation page for {label_model} with objects {object_model}"
                    )
                soup = bs4.BeautifulSoup(response.content.decode(), features="html.parser")
                form = soup.find("form", {"id": "label-confirmation-form"})
                post_data = self.get_form_data(form)
                post_data["_confirmation_yes_button"] = ""
                response = self.client.post(
                    url,
                    data=post_data,
                    follow=True,
                )
        else:
            if format == "true_pdf":
                format = "pdf"
            response = self.client.get(
                reverse(f"labels:{object_type}", args=(label_model.pk, object_model.pk)) + f"?format={format}",
                )

        self.assertLess(response.status_code, 400)
        self.assert_no_warning(response)

        err_msg = "Error creating labels"
        if err_msg.encode() in response.content:
            idx = response.content.find(err_msg.encode())
            raise AssertionError(f"{err_msg}: {response.content[idx:idx + 5000]}")

        return response
