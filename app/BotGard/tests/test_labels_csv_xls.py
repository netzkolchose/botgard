import csv
from io import StringIO, BytesIO

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.admindocs.views import simplify_regex

import xlrd

from labels.models import LabelDefinition
from botman.models import BotanicGarden

from .fixtures import create_test_fixtures


class TestLabelsCSV(TestCase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def test_label_csv(self):
        self.assertTrue(
            self.client.login(username="User1", password="the-secret"),
            "failed to log in"
        )

        label_model = LabelDefinition.objects.get(id_name="A2")

        self.assert_table(
            label_model,
            "garden", BotanicGarden.objects.get(name="Garden 1"),
            ["Line 1", "Line 2", "Line 3", "----", "Line 4"],
        )

        self.assert_table(
            label_model,
            "garden", BotanicGarden.objects.get(name="Garden 2"),
            ["Linä 1", "Line,2", "Line\\n'3", "----", "Line\"4"],
        )

    def assert_table(self, label_model: LabelDefinition, object_type: str, object_model, expected_line: list):
        self.assert_csv(label_model, object_type, object_model, expected_line)
        self.assert_xls(label_model, object_type, object_model, expected_line)

    def assert_csv(self, label_model: LabelDefinition, object_type: str, object_model, expected_line: list):
        response = self.client.get(
            reverse(f"labels:{object_type}", args=(label_model.pk, object_model.pk)) + "?format=csv",
        )
        fp = StringIO(response.content.decode("utf-8"))
        try:
            lines = list(csv.reader(fp))
            self.assertEqual(1, len(lines), "expected one table line")
            self.assertEqual(expected_line, lines[0])
        except Exception:
            fp.seek(0)
            print(f"RENDERED RESPONSE:\n{fp.read()}")
            raise

    def assert_xls(self, label_model: LabelDefinition, object_type: str, object_model, expected_line: list):
        response = self.client.get(
            reverse(f"labels:{object_type}", args=(label_model.pk, object_model.pk)) + "?format=xls",
            )
        try:
            book = xlrd.open_workbook(file_contents=response.content, encoding_override="utf-8")
            sheet = book.sheet_by_index(0)
            lines = [
                [v.value for v in row]
                for row in sheet.get_rows()
            ]
            self.assertEqual(1, len(lines), "expected one table line")
            self.assertEqual(expected_line, lines[0])
        except Exception:
            print("RENDERED RESPONSE:")
            print(response.content)
            raise
