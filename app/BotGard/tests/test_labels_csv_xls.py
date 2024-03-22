import csv
from io import StringIO, BytesIO
from typing import List

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.admindocs.views import simplify_regex

import xlrd

from labels.models import LabelDefinition
from labels.mass_action import render_mass_labels_action
from labels.admin import LabelDefinitionAdmin
from botman.models import BotanicGarden

from .fixtures import create_test_fixtures


class TestLabelsCSV(TestCase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def test_label_single(self):
        self.assertTrue(
            self.client.login(username="User1", password="the-secret"),
            "failed to log in"
        )

        label_model = LabelDefinition.objects.get(id_name="A2")

        self.assert_table(
            label_model,
            "garden", BotanicGarden.objects.get(name="Garden 1"),
            [
                ["Address 1", "Address 2", "Address 3", "Nothing", "Address 4"],
                ["Line 1", "Line 2", "Line 3", "----", "Line 4"],
            ],
        )

        self.assert_table(
            label_model,
            "garden", BotanicGarden.objects.get(name="Garden 2"),
            [
                ["Address 1", "Address 2", "Address 3", "Nothing", "Address 4"],
                ["Linä 1", "Line,2", "Line\\n'3", "----", "Line\"4"],
            ]
        )

    def test_label_mass_action(self):
        self.assertTrue(
            self.client.login(username="User1", password="the-secret"),
            "failed to log in"
        )

        label_model = LabelDefinition.objects.get(id_name="A2")

        self.assert_table(
            label_model,
            "garden",
            [
                BotanicGarden.objects.get(name="Garden 1"),
                BotanicGarden.objects.get(name="Garden 2"),
            ],
            [
                ["Address 1", "Address 2", "Address 3", "Nothing", "Address 4"],
                ["Line 1", "Line 2", "Line 3", "----", "Line 4"],
                ["Linä 1", "Line,2", "Line\\n'3", "----", "Line\"4"],
            ]
        )

    def assert_table(
            self, label_model: LabelDefinition, object_type: str, object_model, expected_lines: List[List[str]]
    ):
        self.assert_csv(label_model, object_type, object_model, expected_lines)
        self.assert_xls(label_model, object_type, object_model, expected_lines)

    def assert_csv(
            self, label_model: LabelDefinition, object_type: str, object_model, expected_lines: List[List[str]]
    ):
        response = self.get_label_response(label_model, object_type, object_model, "csv")
        fp = StringIO(response.content.decode("utf-8"))
        try:
            lines = list(csv.reader(fp))
            self.assertEqual(len(expected_lines), len(lines), f"expected {len(expected_lines)} table lines")
            self.assertEqual(expected_lines, lines)
        except Exception:
            fp.seek(0)
            print(f"RENDERED RESPONSE:\n{fp.read()}")
            raise

    def assert_xls(self, label_model: LabelDefinition, object_type: str, object_model, expected_lines: List[List[str]]):
        response = self.get_label_response(label_model, object_type, object_model, "xls")

        try:
            book = xlrd.open_workbook(file_contents=response.content, encoding_override="utf-8")
            sheet = book.sheet_by_index(0)
            lines = [
                [v.value for v in row]
                for row in sheet.get_rows()
            ]
            self.assertEqual(len(expected_lines), len(lines), f"expected {len(expected_lines)} table lines")
            self.assertEqual(expected_lines, lines)
        except Exception:
            print("RENDERED RESPONSE:")
            print(response.content)
            raise

    def get_label_response(self, label_model: LabelDefinition, object_type: str, object_model, format: str):
        if isinstance(object_model, list):
            if object_type == "garden":
                url = reverse("admin:botman_botanicgarden_changelist")
            else:
                url = reverse("admin:individuals_individual_changelist")
            return self.client.post(
                url,
                data={
                    "action": f"label_{label_model.id_name}_{format}",
                    "_selected_action": [str(o.pk) for o in object_model],
                }
            )
        else:
            return self.client.get(
                reverse(f"labels:{object_type}", args=(label_model.pk, object_model.pk)) + f"?format={format}",
            )