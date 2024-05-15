import re
import subprocess
import tempfile
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

    def assert_pdf_size(self, pdf_data: bytes, expected_size: List[Union[int, float]]):
        with tempfile.TemporaryDirectory() as path:
            filename = Path(path) / "label.pdf"
            filename.write_bytes(pdf_data)
            result = subprocess.check_output(["pdfinfo", str(filename)]).decode()
            match = re.match(r".*Page size:\s+(\d+\.?\d*)\sx\s(\d+.?\d*).*", result.replace("\n", " "))
            if not match:
                raise AssertionError(f"Page size not found in pdfinfo result: {result}")
            page_size = [float(g) for g in match.groups()]
            self.assertEqual(list(expected_size), page_size, "PDF page size does not match")

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