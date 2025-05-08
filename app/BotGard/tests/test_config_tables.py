import json
from typing import List

from django.test import TestCase, Client
from django.urls import reverse
from django.http.response import HttpResponse

import bs4

from .fixtures import create_test_fixtures


class TestConfigTables(TestCase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def setUp(self):
        self.assertTrue(
            self.client.login(username="User1", password="the-secret"),
            "failed to log in"
        )

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

    def assert_change_changelist_columns(self, app_name: str, model_name: str, new_columns: List[str]):
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

        self.assert_changelist_columns(app_name, model_name, new_columns)

    def test_config_table_garden(self):
        self.assert_changelist_columns("botman", "botanicgarden", [
            'change_link_decorator', 'name', 'code', 'phone',
            'website_link_decorator', 'email_link_decorator',
            'label_link_decorator', 'delete_link_decorator',
        ])

        self.assert_change_changelist_columns("botman", "botanicgarden", [
            'address', 'change_link_decorator',
            'full_name_generated', 'catalog_date_generated',
            'num_orders_generated',
        ])


    def test_config_table_individual(self):
        self.assert_changelist_columns("individuals", "individual", [
            'change_link_decorator', 'accession_number', 'accession_extension',
            'ipen_generated', 'species_link_decorator', 'departments_decorator',
            'is_alive', 'source', 'etikett_link_decorator'
        ])

        self.assert_change_changelist_columns("individuals", "individual", [
            'image_decorator', 'change_link_decorator',
            'delete_link_decorator', 'etikett_detail_decorator',
            'territories_decorator',
        ])

