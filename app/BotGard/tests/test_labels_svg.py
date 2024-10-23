import re
import subprocess
import tempfile
import zipfile
import io
from pathlib import Path
from typing import List, Union

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.admindocs.views import simplify_regex

from labels.models import LabelDefinition
from labels.mass_action import render_mass_labels_action
from labels.admin import LabelDefinitionAdmin
from botman.models import BotanicGarden

from .fixtures import create_test_fixtures


class TestLabelsSVG(TestCase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def test_svg_label_single(self):
        self.assertTrue(
            self.client.login(username="User1", password="the-secret"),
            "failed to log in"
        )

        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="A1"),
            "garden",
            BotanicGarden.objects.get(name="Garden 1"),
            "pdf",
        )
        self.assert_pdf_size(response.content, [252, 102])

    def test_svg_label_multi(self):
        self.assertTrue(
            self.client.login(username="User1", password="the-secret"),
            "failed to log in"
        )

        # --- multiple PDFS as zip from change-list action ---

        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="A1"),
            "garden",
            [BotanicGarden.objects.get(name="Garden 1"), BotanicGarden.objects.get(name="Garden 2")],
            "pdf",
        )
        self.assertEqual("application/zip", response.headers["Content-Type"])
        fp = io.BytesIO(response.content)
        with zipfile.ZipFile(fp) as zf:
            self.assertEqual(2, len(zf.filelist))
            for fileinfo in zf.filelist:
                self.assertTrue(fileinfo.filename.endswith(".pdf"), fileinfo)
                with zf.open(fileinfo.filename) as fp:
                    self.assert_pdf_size(fp.read(), [252, 102])

        # single selected file in change-list action returns no zip
        response = self.get_label_response(
            LabelDefinition.objects.get(id_name="A1"),
            "garden",
            [BotanicGarden.objects.get(name="Garden 1")],
            "pdf",
        )
        self.assert_pdf_size(response.content, [252, 102])

    def assert_pdf_size(self, pdf_data: bytes, expected_size: List[int]):
        with tempfile.TemporaryDirectory() as path:
            filename = Path(path) / "label.pdf"
            filename.write_bytes(pdf_data)
            result = subprocess.check_output(["pdfinfo", str(filename)]).decode()
            match = re.match(r".*Page size:\s+(\d+\.?\d*)\sx\s(\d+.?\d*).*", result.replace("\n", " "))
            if not match:
                raise AssertionError(f"Page size not found in pdfinfo result: {result}")
            page_size = [int(float(g)) for g in match.groups()]
            self.assertEqual(list(expected_size), page_size, "PDF page size does not match")

    def get_label_response(self, label_model: LabelDefinition, object_type: str, object_model, format: str):
        if isinstance(object_model, list):
            if object_type == "garden":
                url = reverse("admin:botman_botanicgarden_changelist")
            else:
                url = reverse("admin:individuals_individual_changelist")
            response = self.client.post(
                url,
                data={
                    "action": f"label_{label_model.id_name}",
                    "_selected_action": [str(o.pk) for o in object_model],
                },
                follow=True,
            )
        else:
            response = self.client.get(
                reverse(f"labels:{object_type}", args=(label_model.pk, object_model.pk)) + f"?format={format}",
            )

        self.assertLess(response.status_code, 400)

        err_msg = "Error creating labels"
        if err_msg.encode() in response.content:
            idx = response.content.find(err_msg.encode())
            raise AssertionError(f"{err_msg}: {response.content[idx:idx + 5000]}")

        return response
