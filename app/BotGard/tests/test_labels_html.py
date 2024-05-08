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

        response = self.get_label_response(label_model, "individual", Individual.objects.get(accession_number=1000), "html")
        print(response.content)

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