import django.contrib.admin
import django.apps

from config_app.models import KeyValue
from .base import *
import config_app


class TestConfigApp(TestBase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def setUp(self):
        self.assertTrue(
            self.client.login(username="User1", password="the-secret"),
            "failed to log in"
        )

    def test_individual_ipen_generated(self):
        self.assertEqual("AU-0-GARD1-1000", Individual.objects.get(accession_number="1000").ipen_generated)
        self.assertEqual("IT-0-GARD2-1001", Individual.objects.get(accession_number="1001").ipen_generated)

    def test_individual_ipen_generated_custom_jena(self):
        """test custom setting used in jena"""
        KeyValue.objects.create(key="ipen_creation_individual", type="n", value_normal_text="""
"{}-{}-{}-{}".format(
    str.upper(self.ipen_country),
    str.upper(self.ipen_transfer_restricted),
    str.upper(self.ipen_garden_code.code or "XX"),
    self.ipen_accession_number,
    ) + (
        f"-{self.accession_extension}" 
        if self.accession_extension and self.ipen_garden_code.code == "GARD2" 
        else ""
    )
""")
        for accession_number, expected_ipen in (
            ("1000", "AU-0-GARD1-1000"),
            ("1001", "IT-0-GARD2-1001-10"),
            ("1002", "CZ-0-GARD1-1002"),
            ("1003", "ES-0-GARD2-1003-W"),
        ):
            model = Individual.objects.get(accession_number=accession_number)
            model.save()
            self.assertEqual(expected_ipen, model.ipen_generated)

    def test_entry_ipen_generated(self):
        model = Entry.objects.get(accession_number="10")
        self.assertEqual("xx-x-x-10", model.ipen_generated)
        model.ipen_country = "AU"
        model.ipen_transfer_restricted = "1"
        model.ipen_garden_code = "1 (GARD2/Garden 2)"  # what autocomplete would fill into changeform
        model.save()
        model.refresh_from_db()
        self.assertEqual("AU-1-GARD2-10", model.ipen_generated)

    def test_entry_ipen_generated_custom(self):
        # some really wierd ipen-generator
        KeyValue.objects.create(key="ipen_creation_entry", type="n", value_normal_text="""
f"{len(self.ipen_generated)}-Dobbstown-{self.ipen_generated}"
""")
        model = Entry.objects.get(accession_number="10")
        model.save()
        self.assertEqual("9-Dobbstown-xx-x-x-10", model.ipen_generated)
        model.save()
        self.assertEqual("21-Dobbstown-9-Dobbstown-xx-x-x-10", model.ipen_generated)

    def test_config_app_admin(self):
        from config_app.management.commands.botgard_update_config import update_config_in_database
        update_config_in_database()

        for config_key, expected_visible in (
                ("site_branding", {"value_en": True, "value_json": False, "value_normal_text": False}),
                ("accession_generation", {"value_en": False, "value_json": True, "value_normal_text": False}),
                ("ipen_creation_individual", {"value_en": False, "value_json": False, "value_normal_text": True}),
        ):
            response = self.client.get(reverse(
                "admin:config_app_keyvalue_change",
                args=(KeyValue.objects.get(key=config_key).pk, )
            ))
            form = self.get_soup(response.content).find("form", {"id": "keyvalue_form"})
            for field_name in expected_visible.keys():
                elem = form.find("div", {"class": f"field-{field_name}"})
                self.assertTrue(elem, f"config_key='{config_key}', field_name='{field_name}'")
                class_str = elem.attrs["class"]
                if expected_visible[field_name]:
                    self.assertNotIn("hidden", class_str)
                else:
                    self.assertIn("hidden", class_str)
