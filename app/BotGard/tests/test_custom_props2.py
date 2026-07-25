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

    def test_customprops_not_visible(self):
        form = self.get_changeform("botman", "botanicgarden")
        self.assertTrue(form.soup.find("div", {"class": "field-custom_values_bool"}))

        CustomProperty.objects.all().delete()
        form.request()
        self.assertFalse(form.soup.find("div", {"class": "field-custom_values_bool"}))

    def test_customprops_correct_widgets(self):
        CustomProperty.objects.all().delete()

        prop1 = self.create_custom_property(BotanicGarden, "1", type="text")
        prop2 = self.create_custom_property(BotanicGarden, "2", type="text_long")
        prop3 = self.create_custom_property(BotanicGarden, "3", type="bool")
        # text or text_long with choices renders select
        prop4 = self.create_custom_property(BotanicGarden, "4", type="text", choices=["A", "B", "C"])
        prop5 = self.create_custom_property(BotanicGarden, "5", type="text_long", choices=["D", "E", "F"])
        # bool ignores choices and stays a checkbox
        prop6 = self.create_custom_property(BotanicGarden, "6", type="bool", choices=["A", "B", "C"])

        form = self.get_changeform("botman", "botanicgarden", BotanicGarden.objects.get(code="GARD1").pk)

        self.assertEqual("text", form.get_form_field(f"custom-property-{prop1.pk}").type)
        self.assertEqual("textarea", form.get_form_field(f"custom-property-{prop2.pk}").type)
        self.assertEqual("checkbox", form.get_form_field(f"custom-property-{prop3.pk}").type)
        self.assertEqual("select", form.get_form_field(f"custom-property-{prop4.pk}").type)
        self.assertEqual("select", form.get_form_field(f"custom-property-{prop5.pk}").type)
        self.assertEqual("checkbox", form.get_form_field(f"custom-property-{prop6.pk}").type)

        form.save({f"custom-property-{prop1.pk}": "Bla"})
        form.save({f"custom-property-{prop2.pk}": "BlaBla"})
        form.save({f"custom-property-{prop3.pk}": True})
        form.save({f"custom-property-{prop4.pk}": "D"}, expect_validation_errors=True)
        form.save({f"custom-property-{prop4.pk}": "B"})
        form.save({f"custom-property-{prop5.pk}": "A"}, expect_validation_errors=True)
        form.save({f"custom-property-{prop5.pk}": "E"})
        form.save({f"custom-property-{prop6.pk}": True})
        form.assert_data({
            f"custom-property-{prop1.pk}": "Bla",
            f"custom-property-{prop2.pk}": "BlaBla",
            f"custom-property-{prop3.pk}": True,
            f"custom-property-{prop4.pk}": "B",
            f"custom-property-{prop5.pk}": "E",
            f"custom-property-{prop6.pk}": True,
        })

    def test_customprops_admin_garden(self):
        prop1 = CustomProperty.objects.get(name="garden_important")  # a bool prop
        prop2 = self.create_custom_property(BotanicGarden, "garden_comment")
        prop3 = self.create_custom_property(BotanicGarden, "garden_select", choices=["A", "B", "C"])
        prop4 = self.create_custom_property(BotanicGarden, "garden_long", type="text_long")
        prop5 = self.create_custom_property(BotanicGarden, "garden_user", type="user")

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
            f"custom-property-{prop5.pk}": None,
            "email": None,
            "name": None,
            "number": "3",
            "phone": None,
            "website": None,
        })
        self.assertEqual("checkbox", form.get_form_field(f"custom-property-{prop1.pk}").type)
        self.assertEqual("text", form.get_form_field(f"custom-property-{prop2.pk}").type)
        self.assertEqual("select", form.get_form_field(f"custom-property-{prop3.pk}").type)
        self.assertEqual("textarea", form.get_form_field(f"custom-property-{prop4.pk}").type)
        self.assertEqual("select", form.get_form_field(f"custom-property-{prop5.pk}").type)

        new_data = {
            "address": "Adr1",
            "bgci_id": "555",
            "code": "G23",
            "comment": "Nothing really",
            f"custom-property-{prop1.pk}": True,
            f"custom-property-{prop2.pk}": "Extra bits",
            f"custom-property-{prop3.pk}": "B",
            f"custom-property-{prop4.pk}": "Long text",
            f"custom-property-{prop5.pk}": "User1",
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
        self.assertEqual(
            UserModel.objects.get(username="User1"),
            getattr(instance, f"custom_property_{prop5.pk}"),
        )
        form.assert_data(new_data)

        form.save({
            f"custom-property-{prop3.pk}": "Unknown choice",
        }, expect_validation_errors=True)

        form.save({
            f"custom-property-{prop5.pk}": "Unknown user",
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

    def test_customprops_mandatory(self):
        CustomProperty.objects.all().delete()

        prop1 = self.create_custom_property(BotanicGarden, "text", type="text")
        prop2 = self.create_custom_property(BotanicGarden, "long", type="text_long")
        prop3 = self.create_custom_property(BotanicGarden, "bool", type="bool")
        prop4 = self.create_custom_property(BotanicGarden, "choices", type="text", choices=["A", "B", "C"])
        prop5 = self.create_custom_property(BotanicGarden, "user", type="user")

        form = self.get_changeform(
            "botman", "botanicgarden", BotanicGarden.objects.get(code="GARD1").pk,
        )
        form.assert_data({
            f"custom-property-{prop1.pk}": None,
            f"custom-property-{prop2.pk}": None,
            f"custom-property-{prop3.pk}": None,
            f"custom-property-{prop4.pk}": None,
            f"custom-property-{prop5.pk}": None,
        })
        form.save()

        for prop in (prop1, prop2, prop3, prop4, prop5):
            prop.required = True
            prop.save()
            form.save(expect_validation_errors=True)
            value = prop.name
            if prop == prop3:
                value = True
            elif prop == prop4:
                value = "B"
            elif prop == prop5:
                value = "User1"
            form.save({
                f"custom-property-{prop.pk}": value,
            })

        form.assert_data({
            f"custom-property-{prop1.pk}": "text",
            f"custom-property-{prop2.pk}": "long",
            f"custom-property-{prop3.pk}": True,
            f"custom-property-{prop4.pk}": "B",
            f"custom-property-{prop5.pk}": "User1",
        })

    def TODO_test_customprops_ordering(self):
        """
        Just some testing ground to find a way to sort by CustomProps values
        without creating duplicate rows in the queryset
        """
        CustomProperty.objects.all().delete()

        prop1 = self.create_custom_property(BotanicGarden, "text1", type="text")
        prop2 = self.create_custom_property(BotanicGarden, "text2", type="text")

        BotanicGarden.objects.get(code="GARD1").custom_values_text.set([
            PropertyValueText.objects.create(property=prop1, value="b"),
            PropertyValueText.objects.create(property=prop2, value="1"),
        ])
        BotanicGarden.objects.get(code="GARD1").custom_values_text.set([
            PropertyValueText.objects.create(property=prop1, value="a"),
            PropertyValueText.objects.create(property=prop2, value="2"),
        ])

        qset = (
            BotanicGarden.objects.all()
            .annotate(
                cp1=models.F("custom_values_text__value"),
                is_cp1=models.Q(custom_values_text__property__pk=prop1.pk),
                is_cp2=models.Q(custom_values_text__property__pk=prop2.pk),
            )
        )
        qset = qset.filter(is_cp1=True) | qset.filter(is_cp1=None)
        qset = (
            qset
            #.annotate(f"custom_prop_{prop1.pk}")
            #.order_by("custom_values_text__value")
            .order_by("cp1")
            #.order_by(f"custom_prop_{prop1.pk}")
        )
        for m in qset:
            print(m, m.cp1, m.is_cp1)

