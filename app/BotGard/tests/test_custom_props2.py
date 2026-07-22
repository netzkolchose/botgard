import django.contrib.admin
import django.apps

from .base import *

class TestCustomProps2(TestBase):

    @classmethod
    def setUpTestData(cls):
        fixtures.create_test_fixtures()

    def setUp(self):
        self.login(username="User1")

    def test_customprops_admin_logentry_individual(self):
        instance = Individual.objects.get(accession_number=1000)

        prop1 = CustomProperty.objects.get(name="individual_comment")
        prop2 = CustomProperty.objects.create(
            model="individuals.Individual",
            type="text",
            name="individual_comment2",
        )

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
        form.post()

        # check that property is unchanged
        self.assertEqual(
            orig_props,
            {
                p.pk: p.value
                for p in instance.custom_values_text.all()
            }
        )

        # check changes to both property values
        form.post({
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
        form.post({
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
        form.post({
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
