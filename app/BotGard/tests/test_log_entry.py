from typing import Sequence

from .base import *

class TestLogEntry(TestBase):

    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        fixtures.create_test_fixtures()

    def assert_no_log_entry(self, instance: models.Model):
        """Assert that last LogEntry is empty"""
        ct = ContentType.objects.get_for_model(instance.__class__)
        qset = LogEntry.objects.filter(content_type=ct, object_id=instance.pk)
        if qset.exists():
            entry = qset.order_by("action_time").last()
            if entry.change_message and entry.change_message != "[]":
                raise AssertionError(f"Expected empty LogEntry for '{instance}', got: {entry.change_message}")

    def assert_no_log_entries(self, instance: models.Model):
        """Asert that no (or empty) LogEntry entries exist"""
        ct = ContentType.objects.get_for_model(instance.__class__)
        qset = LogEntry.objects.filter(content_type=ct, object_id=instance.pk)
        if qset.exists():
            if any(entry.change_message != '[]' for entry in qset):
                entries = "\n".join(
                    f"{e.action_time}: '{e.object_repr}': {e.change_message}"
                    for e in qset
                )
                raise AssertionError(f"Expected no LogEntry for '{instance}', got:\n{entries}")

    def assert_log_entry_changed_fields(self, instance: models.Model, fields: Sequence[str]):
        ct = ContentType.objects.get_for_model(instance.__class__)
        qset = LogEntry.objects.filter(content_type=ct, object_id=instance.pk)
        if not qset.exists():
            raise AssertionError(f"No LogEntry for {instance}")
        entry = qset.order_by("action_time").last()
        found = False
        try:
            messages = json.loads(entry.change_message)
        except json.JSONDecodeError:
            messages = []
        for msg in messages:
            if msg.get("changed"):
                self.assertEqual(
                    sorted(fields),
                    sorted(msg["changed"]["fields"]),
                )
                found = True
                break
        if not found:
            raise AssertionError(f"No changed fields in LogEntry for {instance}. change_message={entry.change_message}")

    def test_log_entry_no_change(self):
        self.login("User1")
        for model_class in (
                BotanicGarden, BGCIGarden, OutgoingOrder, ExternalCatalog,
                Literature, Project, Family, Species, Territory, Department,
                Entry, Individual, Outplanting, LabelDefinition, Herbarium, HerbariumSpecimen,
                BasicTicket, SeedCatalog,
        ):
            #print("----", model_class)
            instance = model_class.objects.first()
            self.assert_no_log_entries(instance)

            cf = self.get_changeform(model_class._meta.app_label, model_class._meta.model_name, instance.pk)
            cf.save()

            self.assert_no_log_entries(instance)

    def test_log_entry_individual_customprop(self):
        indi = Individual.objects.get(accession_number=1000)
        self.assert_no_log_entries(indi)
        prop1 = CustomProperty.objects.get(name="individual_comment")
        prop2 = CustomProperty.objects.create_for_model(indi, type="bool", name="individual_check")
        prop3 = CustomProperty.objects.create_for_model(indi, type="user", name="individual_user")

        self.login("User1")
        cf = self.get_changeform("individuals", "individual", indi.pk)

        cf.save()
        self.assert_no_log_entry(indi)

        cf.save({f"custom-property-{prop1.pk}": "A bush"})
        indi.refresh_from_db()
        self.assertEqual("A bush", indi.custom_property(prop1.name))
        self.assert_log_entry_changed_fields(indi, [prop1.name])

        cf.save({f"custom-property-{prop2.pk}": True})
        indi.refresh_from_db()
        self.assertEqual(True, indi.custom_property(prop2.name))
        self.assert_log_entry_changed_fields(indi, [prop2.name])

        cf.save({f"custom-property-{prop3.pk}": User.objects.get(username="User1")})
        indi.refresh_from_db()
        self.assertEqual(User.objects.get(username="User1"), indi.custom_property(prop3.name))
        self.assert_log_entry_changed_fields(indi, [prop3.name])

        cf.save({f"custom-property-{prop2.pk}": False})
        indi.refresh_from_db()
        self.assertEqual(False, indi.custom_property(prop2.name))
        self.assert_log_entry_changed_fields(indi, [prop2.name])

        cf.save({
            f"custom-property-{prop1.pk}": "A fungus",
            f"custom-property-{prop2.pk}": True,
            f"custom-property-{prop3.pk}": User.objects.get(username="User2"),
        })
        indi.refresh_from_db()
        self.assertEqual("A fungus", indi.custom_property(prop1.name))
        self.assertEqual(True, indi.custom_property(prop2.name))
        self.assertEqual(User.objects.get(username="User2"), indi.custom_property(prop3.name))
        self.assert_log_entry_changed_fields(indi, [prop1.name, prop2.name, prop3.name])

        cf.save()
        self.assert_no_log_entry(indi)
