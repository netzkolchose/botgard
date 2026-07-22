import pprint

import django.contrib.admin
import django.apps

from .base import *

class TestCustomProps2(TestBase):

    @classmethod
    def setUpTestData(cls):
        fixtures.create_test_fixtures()

    def setUp(self):
        self.login(username="User1")

    #@log_requests
    def test_customprops_admin_garden(self):
        prop1 = CustomProperty.objects.get(name="garden_important")  # a bool prop
        prop2 = self.create_custom_property(BotanicGarden, "garden_comment")
        prop3 = self.create_custom_property(BotanicGarden, "garden_select", choices=["A", "B", "C"])
        prop4 = self.create_custom_property(BotanicGarden, "garden_long", type="text_long")

        form = self.get_changeform("botman", "botanicgarden")
        #pprint.pprint(form.get_data())
        form.assert_data({
            "address": None,
            "bgci_id": None,
            "code": None,
            "comment": None,
            f"custom-property-{prop1.pk}": False,
            f"custom-property-{prop2.pk}": None,
            f"custom-property-{prop3.pk}": None,
            f"custom-property-{prop4.pk}": None,
            "email": None,
            "name": None,
            "number": "3",
            "phone": None,
            "website": None,
        })
        new_data = {
            "address": "Adr1",
            "bgci_id": "555",
            "code": "G23",
            "comment": "Nothing really",
            f"custom-property-{prop1.pk}": True,
            f"custom-property-{prop2.pk}": "Extra bits",
            f"custom-property-{prop3.pk}": "B",
            f"custom-property-{prop4.pk}": "Long text",
            "email": "a@b.cd",
            "name": "Garden 23",
            "number": "4",
            "phone": "12345",
            "website": "https://garden.23.com",
        }
        form.save(new_data)
        instance = BotanicGarden.objects.get(pk=form.pk)
        self.assertEqual(True, getattr(instance, f"custom_property_{prop1.pk}"))
        self.assertEqual("Extra bits", getattr(instance, f"custom_property_{prop2.pk}"))
        self.assertEqual("B", getattr(instance, f"custom_property_{prop3.pk}"))
        self.assertEqual("Long text", getattr(instance, f"custom_property_{prop4.pk}"))
        form.assert_data(new_data)

        form.save({
            f"custom-property-{prop3.pk}": "Unknown choice",
        }, expect_validation_errors=True)

    def test_customprops_admin_individual(self):
        instance = Individual.objects.get(accession_number=1000)

        prop1 = CustomProperty.objects.get(name="individual_comment")
        prop2 = self.create_custom_property(Individual, "individual_comment2")

        # check that one custom property is set for this instance
        orig_props = {
            p.pk: p.value
            for p in instance.custom_values_text.all()
        }
        self.assertEqual(
            {
                self.get_property_value("individual_comment", instance).pk: "A tree"
            },
            orig_props
        )

        # post changeform as-is
        form = self.get_changeform("individuals", "individual", instance.pk)
        form.save()

        # check that property is unchanged
        self.assertEqual(
            orig_props,
            {
                p.pk: p.value
                for p in instance.custom_values_text.all()
            }
        )

        # check changes to both property values
        form.save({
            f"custom-property-{prop1.pk}": "Changed",
            f"custom-property-{prop2.pk}": "Changed2",
        })
        v1_pk = self.get_property_value("individual_comment", instance).pk
        v2_pk = self.get_property_value("individual_comment2", instance).pk
        self.assertEqual(
            {
                v1_pk: "Changed",
                v2_pk: "Changed2",
            },
            {
                p.pk: p.value
                for p in instance.custom_values_text.all()
            }
        )
        # make sure the v1 was not recreated, just changed
        self.assertIn(v1_pk, orig_props)

        instance.refresh_from_db()
        self.assertEqual(getattr(instance, f"custom_property_{prop1.pk}"), "Changed")
        self.assertEqual(getattr(instance, f"custom_property_{prop2.pk}"), "Changed2")

        # remove both
        form.save({
            f"custom-property-{prop1.pk}": "",
            f"custom-property-{prop2.pk}": "",
        })
        self.assertEqual(
            {},
            {
                p.pk: p.value
                for p in instance.custom_values_text.all()
            }
        )
        # make sure no value keeps dangling around
        self.assertEqual(
            0,
            PropertyValueText.objects.filter(property__in=[prop1, prop2]).count()
        )

        # set only 2nd
        form.save({
            f"custom-property-{prop1.pk}": "",
            f"custom-property-{prop2.pk}": "Bob!",
        })
        v2_pk2 = self.get_property_value("individual_comment2", instance).pk
        self.assertNotEqual(v2_pk, v2_pk2)
        self.assertEqual(
            {
                v2_pk2: "Bob!"
            },
            {
                p.pk: p.value
                for p in instance.custom_values_text.all()
            }
        )
        self.assertEqual(
            1,
            PropertyValueText.objects.filter(property__in=[prop1, prop2]).count()
        )
        #pprint.pprint(self.get_log_entries("User1"))
