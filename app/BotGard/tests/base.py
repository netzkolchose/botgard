import copy
import dataclasses
import re
import io
import csv
import json
import pprint
import zipfile
import urllib.parse
import secrets
import webbrowser
import itertools
import subprocess
import importlib
from pathlib import Path
import tempfile
from typing import Dict, Set, Optional, Type, Callable, Any, Literal

import django.contrib.admin.sites
from django.test import TestCase, Client, override_settings
from django.test.utils import override_settings
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.db import models
from django.utils import timezone
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, Group
from django.contrib.auth import get_user_model
from django.contrib.admin.models import LogEntry
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
from literature.models import *
from meta.models import *

from . import fixtures
from .fixtures import create_permission_group, create_test_fixtures
from config_app.management.commands.botgard_update_config import update_config_in_database
from config_app.models import *
from config_tables.admin import ConfigurableTable


UserModel = get_user_model()


"""
decorator to turn on logging of requests
"""
log_requests = override_settings(MIDDLEWARE=settings.MIDDLEWARE + ["tools.log_middleware.LogRequestMiddleware"])


# models that are not represented in the admin views
INVISIBLE_MODELS = (
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
    "BotGard.passwordresetcode",
    "config_app.propertyvaluetext",
    "config_app.propertyvaluebool",
    "config_app.propertyvalueuser",
    "entrybook.entry_projects",
    "individuals.individual_projects",
    "gis.postgisspatialrefsys",
    "gis.postgisgeometrycolumns",
)


class TestBase(TestCase):

    def get_visible_models(self) -> List[Type[models.Model]]:
        return [
            model for model in django.apps.apps.get_models()
            if model._meta.label_lower not in INVISIBLE_MODELS
        ]

    def get_model_admins(self) -> List[Tuple[Type[models.Model], admin.ModelAdmin]]:
        admins = []
        for klass, admin in django.contrib.admin.site._registry.items():
            admins.append((klass, admin))
        admins.sort(key=lambda t: t[0]._meta.label_lower)
        return admins

    def login(self, username: str, password: str = "the-secret"):
        self.assertTrue(
            self.client.login(username=username, password=password),
            f"failed to log in {username}"
        )

    def get_soup(self, content: Union[str, bytes]) -> bs4.PageElement:
        if isinstance(content, bytes):
            content = content.decode()
        return bs4.BeautifulSoup(content, features="html.parser")

    def get_form_data(self, form: Union[str, bytes, bs4.PageElement]) -> dict:
        if isinstance(form, (str, bytes)):
            form = self.get_soup(form).find("form")

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

    def assert_response(
            self,
            response: HttpResponse,
            status: Optional[int] = None,
    ):
        if status is not None:
            if response.status_code != status:
                raise AssertionError(f"Expected status {status}, got {response.status_code}")

    def assert_no_warning(self, response: HttpResponse):
        for pattern in (
                b'li class="warning"',
                b'p class="error"',
        ):
            if pattern in response.content:
                idx = response.content.index(pattern)
                snippet = response.content[idx: idx + 200]
                raise AssertionError(f"warning/error found in response {response}: {snippet}")

    def get_response_error(self, response: HttpResponse) -> str:
        """
        Find the error displayed in the response

        To get details your test function must run in DEBUG mode, e.g.

            @override_settings(DEBUG=True)
            def test_something(self):
                ...
        """
        soup = self.get_soup(response.content)
        msg = soup.find("h1").text
        elem = soup.find("pre", {"class": "exception_value"})
        if elem:
            msg = f"{msg}\n{elem.text}"
        return msg

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
                soup = self.get_soup(response.content)
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

    def assert_changelist_columns(self, app_name: str, model_name: str, expected_columns: List[str]):
        """
        Assert that the changelist admin view has the expected columns (IDs)
        """
        # check changelist
        response = self.client.get(
            reverse(f"admin:{app_name}_{model_name}_changelist"),
        )
        soup = bs4.BeautifulSoup(response.content, features="html.parser")
        table = soup.find("table", {"id": "result_list"})
        columns = []
        for th in table.find("thead").find("tr").find_all("th"):
            if classes := list(filter(lambda c: c.startswith("column-"), th.attrs["class"])):
                columns.append(classes[0][7:])

        self.assertEqual(
            expected_columns, columns,
            f"\nExpected:{expected_columns}\n\nGot:\n{columns}"
        )

        # check configure-table view
        response = self.client.get(
            reverse(f"admin:{app_name}_{model_name}_configuretable")
        )
        soup = bs4.BeautifulSoup(response.content, features="html.parser")
        columns = []
        for li in soup.find("ul", {"data-testid": "draggable-column-items"}).find_all("li"):
            columns.append(li.attrs["value"])
        self.assertEqual(expected_columns, columns)

        # check configure-table xhr endpoint
        response = self.client.get(
            reverse(f"admin:{app_name}_{model_name}_configuretable_tree")
        )
        soup = bs4.BeautifulSoup(response.content, features="html.parser")
        columns = []
        for inp in soup.find_all("input", {"type": "checkbox"}):
            if inp.attrs.get("checked"):
                columns.append(inp.attrs["id"])

        self.assertEqual(set(expected_columns), set(columns))

        return columns

    def assert_change_changelist_columns(
            self,
            app_name: str,
            model_name: str,
            new_columns: List[str],
            not_in_new_columns: Optional[List[str]] = None,
    ):
        """
        Change the column settings and assert that the change is reflected in admin UI
        """
        response = self.client.get(
            reverse(f"admin:{app_name}_{model_name}_configuretable"),
        )
        soup = bs4.BeautifulSoup(response.content, features="html.parser")
        token = soup.find("input", {"name": "csrfmiddlewaretoken"}).attrs["value"]

        response = self.client.post(
            reverse(f"admin:{app_name}_{model_name}_configuretable"),
            data={
                "csrfmiddlewaretoken": token,
                "settings": json.dumps([
                    [c, c] for c in new_columns
                ]),
            },
        )
        self.assertEqual(302, response.status_code)  # redirects to changelist

        if not not_in_new_columns:
            self.assert_changelist_columns(app_name, model_name, new_columns)
        else:
            self.assert_changelist_columns(
                app_name, model_name,
                [c for c in new_columns if c not in not_in_new_columns]
            )

    def create_custom_property(
            self,
            model: Union[models.Model, Type[models.Model]],
            name: str,
            type: str = "text",
            choices: Optional[List[str]] = None,
    ):
        return CustomProperty.objects.create_for_model(
            model=model,
            type=type,
            name=name,
            choices="\n".join(choices) if choices else "",
        )

    def get_property_value(
            self, property_name: str, instance: models.Model
    ) -> Union[None, PropertyValueBool, PropertyValueText]:
        return PropertyValueText.objects.filter(**{
            "property__name": property_name,
            f"{instance._meta.model_name}_values_text": instance.pk,
        }).first() or PropertyValueBool.objects.filter(**{
            "property__name": property_name,
            f"{instance._meta.model_name}_values_bool": instance.pk,
        }).first()

    def get_log_entries(self, username: Optional[str] = None) -> List[dict]:
        qset = LogEntry.objects.all()
        if username:
            qset = qset.filter(user=UserModel.objects.get(username=username))

        return list(qset.order_by("action_time").values(
            "action_time",
            "user",
            "content_type",
            "object_id",
            "object_repr",
            "action_flag",
            "change_message",
        ))

    def assert_admin_form_errors(self, response: HttpResponse):
        if not response.context:
            raise AssertionError("response has not context to check")

        if adminform := response.context.get("adminform"):
            if adminform.form.errors:
                return

        raise AssertionError(f"No expected form validation errors")

    def assert_no_admin_form_errors(self, response: HttpResponse):
        if response.context:
            if adminform := response.context.get("adminform"):
                if adminform.form.errors:
                    raise AssertionError(f"Form validation errors:\n{adminform.form.errors}")

    def get_changelist(self, app_name: str, model_name: str) -> "ChangeListForm":
        return ChangeListForm(self, app_name, model_name)

    def get_changeform(self, app_name: str, model_name: str, pk: Union[None, str, int] = None) -> "ChangeForm":
        return ChangeForm(self, app_name, model_name, pk)

class ChangeListForm:
    """
    Interface to the django changelist admin interface through html parsing
    """

    @dataclasses.dataclass
    class FormField:
        element: bs4.PageElement
        name: str
        value: str
        hidden: bool
        type: Optional[str] = None
        options: Optional[List[str]] = None
        is_header_filter: bool = True
        disabled: bool = False

    @dataclasses.dataclass
    class Header:
        name: str
        title: str
        filter: Optional["FormField"] = None

    def __init__(self, parent: TestBase, app_name: str, model_name: str):
        self.parent = parent
        self.app_name = app_name
        self.model_name = model_name
        self.url = reverse(f"admin:{self.app_name}_{model_name}_changelist")
        self.query_params = {}
        self.fields: List[ChangeListForm.FormField] = []
        self.headers: List[ChangeListForm.Header] = []
        self.rows: List[Dict[str, Any]] = []
        self.num_pages = 0
        self.request()

    def set_filters(self, params: dict):
        for key, value in params.items():
            field = self.get_form_field(key)
            if field.options:
                self.parent.assertIn(value, field.options)
        self.query_params = params
        self.request()

    def has_action(self, name: str) -> bool:
        sel = self.soup.find("select", {"name": "action"})
        return bool(sel.find("option", {"value": name}))

    def run_action(self, name: str, rows: Union[bool, Tuple[int, int]] = True):
        """
        Select rows, select action and post.

        :param name: str, internal name of the action
        :param rows: either True, to "select-across" all (filtered) entities,
            or a range like (0, 3) to select rows 0, 1, 2
        """
        sel = self.soup.find("select", {"name": "action"})
        if not sel.find("option", {"value": name}):
            raise AssertionError(
                f"Action '{name}' is not in actions list, available actions are: "
                + ", ".join([opt.attrs["value"] for opt in sel.find_all("option") if opt.attrs.get("value")])
            )
        params = QueryDict(mutable=True)
        params["action"] = name

        if rows is True:
            params["select-across"] = "1"

        elif isinstance(rows, (list, tuple)):
            self.parent.assertEqual(2, len(rows), f"Expected 2-tuple, got {rows}")
            for row in self.rows[rows[0]: rows[1]]:
                params.appendlist(row["action-checkbox"].name, row["action-checkbox"].value)

        else:
            raise AssertionError(f"rows must be True or a 2-tuple, got {rows}")

        self.post(params, no_save=True)

    def request(self):
        response = self.parent.client.get(self.url, query_params=self.query_params)
        self.parent.assert_no_warning(response)
        self.parse(response.content.decode())

    def parse(self, html: str):
        self.soup = bs4.BeautifulSoup(html, features="html.parser")
        self.fields = []
        self.rows = []
        self._parse_form()
        self._parse_table()
        self._parse_paginator()

    def get_form_field(self, name_or_element: Union[str, bs4.PageElement]) -> FormField:
        for field in self.fields:
            if field.name == name_or_element or field.element == name_or_element:
                return field
        sorted_names = sorted(f.name for f in self.fields)
        raise AssertionError(f"Form field '{name_or_element}' not found, got only {sorted_names}")

    def get_row(self, **filters) -> Dict[str, Any]:
        row = self.find_row(**filters)
        if not row:
            raise AssertionError(f"Did not find row for filters {filters}")
        return row

    def find_row(self, **filters) -> Optional[Dict[str, Any]]:
        for row in self.rows:
            is_match = True
            for key, value in filters.items():
                if key not in row:
                    raise AssertionError(f"Missing key '{key}' in row {row}")
                if row[key] != value and row[key] != str(value):
                    is_match = False
                    break
            if is_match:
                return row

    def post(self, override_values: Union[None, Dict, QueryDict] = None, no_save: bool = False):
        if override_values is None:
            values = QueryDict(mutable=True)
        elif isinstance(override_values, QueryDict):
            values = copy.deepcopy(override_values)
            values._mutable = True
        elif isinstance(override_values, dict):
            values = QueryDict(mutable=True)
            for k, v in override_values.items():
                values.appendlist(k, v)
        else:
            raise TypeError(f"Expected dict or QueryDict, got {type(override_values).__name__}")

        for field in self.fields:
            if not field.is_header_filter and not field.disabled:
                if not override_values or field.name not in override_values:
                    values.appendlist(field.name, field.value)

        actual_values = QueryDict(mutable=True)
        for key in values.keys():
            field = self.get_form_field(key)
            for value in values.getlist(key):
                if field.type == "checkbox":
                    if isinstance(value, bool):
                        if not value:
                            continue
                        value = "on"
                elif value is None:
                    value = ""
                actual_values.appendlist(key, value)

        url = self.url
        if self.query_params:
            url = f"{url}?{urllib.parse.urlencode(self.query_params)}"

        if no_save and "_save" in actual_values:
            actual_values.pop("_save")

        # don't put a QueryDict there, it only yields the LAST entry of a list value
        response = self.parent.client.post(url, dict(actual_values), follow=True)

        self.parent.assert_response(response, status=200)
        self.parent.assert_no_warning(response)
        self.parse(response.content.decode())

    def _parse_form(self):
        form = self.soup.find("form", {"id": "changelist-form"})
        if not form:
            form_ids = list(filter(bool, [
                form.attrs.get("id")
                for form in self.soup.find_all("form")
            ]))
            raise AssertionError(f"No changelist-form found in {self.url}, found ids: {form_ids}")

        def _add_field(inp: bs4.PageElement, value):
            self.fields.append(self.FormField(
                element=inp,
                name=inp.attrs["name"],
                value=value,
                type=inp.attrs.get("type"),
                hidden="hidden" in inp.attrs or inp.attrs.get("type") == "hidden",
                is_header_filter="filter-form-element" in inp.attrs.get("class", []),
                disabled="disabled" in inp.attrs,
            ))

        for inp in form.find_all("input"):
            if "name" in inp.attrs:
                if inp.attrs.get("type") == "checkbox":
                    if "value" in inp.attrs:
                        value = inp.attrs["value"]
                    else:
                        value = "checked" in inp.attrs
                else:
                    value = inp.attrs["value"]
                _add_field(inp, value)

        for inp in form.find_all("textarea"):
            _add_field(inp, inp.text)

        for inp in form.find_all("select"):
            value = None
            options = []
            for opt in inp.find_all("option"):
                val = opt.attrs.get("value", "")
                options.append(val)
                if "selected" in opt.attrs and value is None:
                    value = val

            _add_field(inp, value)

    def _parse_table(self):
        table = self.soup.find("table", {"id": "result_list"})

        trs = list(table.find("thead").find_all("tr"))
        for i, th in enumerate(trs[0].find_all("th")):
            name = None
            for klass in th.attrs["class"]:
                if klass.startswith("column-"):
                    name = klass[7:]
                elif klass == "action-checkbox-column":
                    name = "action-checkbox"
            self.parent.assertIsNotNone(name, f"In header column: {th}")

            self.headers.append(self.Header(
                name=name,
                title=th.text.strip(),
            ))

        # TODO: they are currently rendered as td, should be th
        for i, th in enumerate(trs[1].find_all("td")):
            if inp := th.find(None, {"class": "filter-form-element"}):
                self.headers[i].filter = self.get_form_field(inp.attrs["name"])

        for tr in table.find("tbody").find_all("tr"):
            row = {}
            for td in itertools.chain(tr.find_all("td"), tr.find_all("th")):
                name = None
                for klass in td.attrs["class"]:
                    if klass == "action-checkbox":
                        name = klass
                    elif klass.startswith("field-"):
                        name = klass[6:]
                if not name:
                    raise AssertionError(f"Unhandled table tbody td {td}")

                value = td.text.strip()
                if inp := td.find("input"):
                    value = self.get_form_field(inp)
                row[name] = value
            self.rows.append(row)

    def _parse_paginator(self):
        p = self.soup.find("p", {"class": "paginator"})
        self.num_pages = len(list(p.find_all("a")))
        if p.find("span", {"class": "this-page"}):
            self.num_pages += 1


class ChangeForm:
    """
    Interface to the django changeform admin interface through html parsing
    """

    @dataclasses.dataclass
    class FormField:
        element: bs4.PageElement
        name: str
        value: str
        hidden: bool
        type: Optional[str] = None
        options: Optional[List[str]] = None
        disabled: bool = False

        @property
        def is_prefix(self) -> bool:
            return "__prefix__" in self.name

        @property
        def is_multiselect(self) -> bool:
            return self.type == "select" and "multiple" in self.element.attrs

    def __init__(self, parent: TestBase, app_name: str, model_name: str, pk: Union[None, int, str]):
        self.pk = pk
        self.parent = parent
        self.app_name = app_name
        self.model_name = model_name
        self.query_params = {}
        self.fields: List[ChangeForm.FormField] = []
        self.request()

    def __str__(self):
        return f"ChangeForm('{self.app_name}.{self.model_name}', pk={self.pk})"

    @property
    def url(self) -> str:
        if self.pk is not None:
            return reverse(f"admin:{self.app_name}_{self.model_name}_change", args=(self.pk, ))
        else:
            return reverse(f"admin:{self.app_name}_{self.model_name}_add")

    def request(self):
        response = self.parent.client.get(self.url, query_params=self.query_params)
        self.parent.assert_no_warning(response)
        self.parse(response)

    def get_data(self) -> dict:
        def _skip_field(f: ChangeForm.FormField) -> bool:
            return (
                    f.name.startswith("initial-")
                or f.name.startswith("_")
                or "__prefix__" in f.name
                or "_FORMS" in f.name
            )
        return {
            f.name: f.value
            for f in self.fields
            if not _skip_field(f)
        }

    def assert_data(self, expected_fields: dict):
        data = self.get_data()
        errors = {}
        for key, expected_value in expected_fields.items():
            if key not in data:
                errors[key] = "* key missing *"
            value = data[key]
            if expected_value is None or expected_value == "":
                if value in ("", "\n"):
                    is_same = True
                else:
                    is_same = not value
            else:
                is_same = value == expected_value
                if isinstance(expected_value, str) and isinstance(value, str):
                    is_same = value.strip() == expected_value.strip()

            if not is_same:
                errors[key] = f"expected {repr(expected_value)} got {repr(value)}"

        if errors:
            raise AssertionError(f"data not as expected: {self}\n{pprint.pformat(errors)}")

    def save(
            self,
            override_values: Union[None, Dict, QueryDict] = None,
            expect_validation_errors: bool = False,
            action_name: str = "_continue",
    ):
        response = self._save(
            override_values=override_values,
            expect_validation_errors=expect_validation_errors,
            action_name=action_name
        )
        self.parse(response)

    def save_as_individual(self):
        """
        Special case for saved Entry -> "Save as individual"
        """
        response = self._save(
            action_name="_saveasindividual",
        )
        self.pk = None
        self.app_name = "individuals"
        self.model_name = "individual"
        self.parse(response)
        self.parent.assertEqual(
            "Add individual",
            self.soup.find("div", {"id": "content"}).find("h1").text,
        )

    def _save(
            self,
            override_values: Union[None, Dict, QueryDict] = None,
            expect_validation_errors: bool = False,
            action_name: str = "_continue",
    ) -> HttpResponse:
        if override_values is None:
            values = QueryDict(mutable=True)
        elif isinstance(override_values, QueryDict):
            values = copy.deepcopy(override_values)
            values._mutable = True
        elif isinstance(override_values, dict):
            values = QueryDict(mutable=True)
            for k, v in override_values.items():
                values.appendlist(k, v)
        else:
            raise TypeError(f"Expected dict or QueryDict, got {type(override_values).__name__}")

        for field in self.fields:
            if not field.disabled:
                if not override_values or field.name not in override_values:
                    if not field.name.startswith("_"):
                        values.appendlist(field.name, field.value)

        actual_values = QueryDict(mutable=True)
        for key in values.keys():
            field = self.get_form_field(key)
            for value in values.getlist(key):
                if field.type == "checkbox":
                    if isinstance(value, bool):
                        if not value:
                            continue
                        value = "on"
                elif value is None:
                    if field.is_multiselect:
                        continue
                    value = ""
                actual_values.appendlist(key, value)

        url = self.url
        if self.query_params:
            url = f"{url}?{urllib.parse.urlencode(self.query_params)}"

        actual_values[action_name] = ""

        # don't put a QueryDict into client.post(), it only yields the LAST entry of a list value
        actual_values = dict(actual_values)

        if self.pk is None:
            response = self.parent.client.post(url, actual_values)
            if expect_validation_errors:
                self.parent.assert_admin_form_errors(response)
                self.parse(response)
                return response
            self.parent.assert_no_admin_form_errors(response)

            # in case of admin/app/model/add, catch the redirect and extract pk
            self.parent.assert_response(response, status=302)
            url = response.headers["location"]
            self.pk = int(re.match(r".*/(\d+)/change/?$", url).groups()[0])
            response = self.parent.client.get(self.url)
        else:
            response = self.parent.client.post(url, actual_values, follow=True)
            # print("RESPONSE", response.status_code, response.headers)

            if expect_validation_errors:
                self.parent.assert_admin_form_errors(response)
                self.parse(response)
                return response

        self.parent.assert_no_admin_form_errors(response)

        self.parent.assert_response(response, status=200)
        self.parent.assert_no_warning(response)
        return response

    def get_form_field(self, name_or_element: Union[str, bs4.PageElement]) -> FormField:
        for field in self.fields:
            if field.name == name_or_element or field.element == name_or_element:
                return field
        sorted_names = sorted(f.name for f in self.fields)
        raise AssertionError(f"Form field '{name_or_element}' not found, got only {sorted_names}")

    def parse(self, response):
        self.soup = bs4.BeautifulSoup(response.content.decode(), features="html.parser")
        self.fields = []
        self._parse_form()

    def _parse_form(self):
        form = self.soup.find("form", {"id": f"{self.model_name}_form"})
        if not form:
            form_ids = list(filter(bool, [
                form.attrs.get("id")
                for form in self.soup.find_all("form")
            ]))
            raise AssertionError(
                f"No changeform with id='{self.model_name}_form' found in {self.url}. Found ids: {form_ids}"
            )

        def _add_field(inp: bs4.PageElement, value, type: Optional[str] = None):
            try:
                self.fields.append(self.FormField(
                    element=inp,
                    name=inp.attrs["name"],
                    value=value,
                    type=type or inp.attrs.get("type"),
                    hidden="hidden" in inp.attrs or inp.attrs.get("type") == "hidden",
                    disabled="disabled" in inp.attrs,
                ))
            except:
                print(inp)
                raise

        for inp in form.find_all("input"):
            if "name" in inp.attrs:
                if inp.attrs.get("type") == "checkbox":
                    value = "checked" in inp.attrs
                else:
                    value = inp.attrs.get("value")
                _add_field(inp, value)

        for inp in form.find_all("textarea"):
            _add_field(inp, inp.text.lstrip("\n") if inp.text else inp.text, type="textarea")

        for inp in form.find_all("select"):
            if inp.attrs.get("name"):
                value = None
                options = []
                for opt in inp.find_all("option"):
                    val = opt.attrs.get("value", "")
                    options.append(val)
                    if "selected" in opt.attrs and value is None:
                        value = val

                _add_field(inp, value, type="select")
