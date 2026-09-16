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
        """
        Make sure that saving an unchanged changeform does not create changed-fields in django's LogEntry
        """
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
        instance = Individual.objects.get(accession_number=1000)
        self.assert_no_log_entries(instance)
        user1 = User.objects.get(username="User1")
        user2 = User.objects.get(username="User2")
        prop1 = CustomProperty.objects.get(name="individual_comment")
        prop2 = CustomProperty.objects.create_for_model(instance, type="bool", name="individual_check")
        prop3 = CustomProperty.objects.create_for_model(instance, type="user", name="individual_user")

        self.login("User1")
        cf = self.get_changeform("individuals", "individual", instance.pk)

        cf.save()
        self.assert_no_log_entry(instance)

        for props in (
                ((prop1, "A bush"), ),
                ((prop2, True), ),
                ((prop3, user1), ),
                ((prop2, False), ),
                ((prop1, "A fungus"), (prop2, True), (prop3, user2), ),
        ):
            cf.save({
                f"custom-property-{prop.pk}": value
                for prop, value in props
            })
            instance.refresh_from_db()
            for prop, value in props:
                self.assertEqual(value, instance.custom_property(prop.name))
            self.assert_log_entry_changed_fields(instance, [prop.name for prop, value in props])

        cf.save()
        self.assert_no_log_entry(instance)

    def test_log_entry_individual_customprop_multi(self):
        instance = Individual.objects.get(accession_number=1000)
        self.assert_no_log_entries(instance)
        user1 = User.objects.get(username="User1")
        user2 = User.objects.get(username="User2")
        prop1a = CustomProperty.objects.get(name="individual_comment")
        prop1b = CustomProperty.objects.create_for_model(instance, type="text_long", name="individual_comment2")
        prop2a = CustomProperty.objects.create_for_model(instance, type="bool", name="individual_check1")
        prop2b = CustomProperty.objects.create_for_model(instance, type="bool", name="individual_check2")
        prop3a = CustomProperty.objects.create_for_model(instance, type="user", name="individual_user1")
        prop3b = CustomProperty.objects.create_for_model(instance, type="user", name="individual_user2")

        self.login("User1")
        cf = self.get_changeform("individuals", "individual", instance.pk)

        cf.save()
        self.assert_no_log_entry(instance)

        for props in (
                ((prop1a, "A bush"), (prop1b, "green"), ),
                ((prop2a, True), (prop2b, True), ),
                ((prop3a, user1), (prop3b, user2)),
                ((prop2a, False), (prop2b, True) ),
                ((prop2a, True), (prop2b, False) ),
                ((prop2a, False), ),
                ((prop1a, "A fungus"), (prop1b, "blue"), (prop2a, True), (prop2b, True), (prop3a, user2), (prop3b, user1)),
        ):
            cf.save({
                f"custom-property-{prop.pk}": value
                for prop, value in props
            })
            instance.refresh_from_db()
            for prop, value in props:
                self.assertEqual(value, instance.custom_property(prop.name))
            self.assert_log_entry_changed_fields(instance, [prop.name for prop, value in props])

        cf.save()
        self.assert_no_log_entry(instance)
