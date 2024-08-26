import re
from pathlib import Path
import tempfile
import subprocess
from typing import List

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.admindocs.views import simplify_regex

import xlrd

from labels.models import LabelDefinition
from labels.mass_action import render_mass_labels_action
from labels.admin import LabelDefinitionAdmin
from individuals.models import Individual

from .fixtures import create_test_fixtures


class TestLabelsHTML(TestCase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def test_label_single(self):
        self.assertTrue(
            self.client.login(username="User1", password="the-secret"),
            "failed to log in"
        )

        label_model = LabelDefinition.objects.get(id_name="I2")

        # single label HTML
        response = self.get_label_response(label_model, "individual", Individual.objects.get(accession_number=1000), "html")
        # print(response.content)
        self.assertIn(b"""<div class="page-break-after">IPEN: AU-0-GARD1-1000</div>""", response.content)  # has object markup
        self.assertIn(b"""<!DOCTYPE html>""", response.content)  # has page markup

        # single label PDF
        response = self.get_label_response(label_model, "individual", Individual.objects.get(accession_number=1000), "pdf")
        #print(response.content)
        self.assert_pdf(response.content, num_pages=1)

        response = self.get_label_response(label_model, "individual", list(Individual.objects.all()), "html")
        # print(response.content)
        self.assertIn(b"""<div class="page-break-after">IPEN: IT-0-GARD2-1001</div>""", response.content)
        self.assertIn(b"""<div class="page-break-after">IPEN: CZ-0-GARD1-1002</div>""", response.content)
        self.assertIn(b"""<!DOCTYPE html>""", response.content)

        response = self.get_label_response(label_model, "individual", list(Individual.objects.all())[:3], "pdf")
        # print(response)
        self.assert_pdf(response.content, num_pages=3)

    def assert_pdf(self, content: bytes, num_pages: int):
        # check at leats number of pages in PDF
        with tempfile.TemporaryDirectory() as path:
            filename = Path(path) / "label.pdf"
            filename.write_bytes(content)
            result = subprocess.check_output(["pdfinfo", str(filename)]).decode()
            match = re.match(r".*Pages:\s+(\d+).*", result.replace("\n", " "))
            if not match:
                raise AssertionError(f"'Pages' not found in pdfinfo result: {result}")
            self.assertEqual(num_pages, int(match.groups()[0]), f"Number of PDF pages does not match, got:\n{result}")

    def get_label_response(self, label_model: LabelDefinition, object_type: str, object_model, format: str):
        if isinstance(object_model, list):
            if object_type == "garden":
                url = reverse("admin:botman_botanicgarden_changelist")
            else:
                url = reverse("admin:individuals_individual_changelist")
            response = self.client.post(
                url,
                data={
                    "action": f"label_{label_model.id_name}_{format}",
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

