from .base import *


class TestCreationFields(TestBase):

    @classmethod
    def setUpTestData(cls):
        cls.user1 = UserModel.objects.create_superuser(
            username="User1",
            password="the-secret",
        )
        cls.user2 = UserModel.objects.create_superuser(
            username="User2",
            password="the-secret",
        )

    def test_creation_fields(self):
        for Model, minimum_fields in (
                (BotanicGarden, {"name": "Garden"}),
                (BGCIGarden, {"name": "Garden", "type": "Garden", "bgci_id": 23, "bgci_data": {}}),
                (Entry, {}),
                (Territory, {"name": "T1", "code": "T1"}),
        ):
            app_name, model_name = Model._meta.label_lower.split(".")
            with self.subTest(f"{app_name}.{model_name}"):

                self.login("User1")
                cf = self.get_changeform(app_name, model_name)
                cf.save(minimum_fields)
                instance = Model.objects.get(pk=cf.pk)
                self.assertEqual(self.user1, instance.created_by)
                self.assertEqual(timezone.now().date(), instance.created_date)
                self.assertEqual(None, instance.modified_by)
                self.assertEqual(None, instance.modified_date)

                self.login("User2")
                for i in range(2):
                    cf = self.get_changeform(app_name, model_name, pk=instance.pk)
                    cf.save()

                    instance.refresh_from_db()
                    self.assertEqual(self.user1, instance.created_by)
                    self.assertEqual(timezone.now().date(), instance.created_date)
                    self.assertEqual(self.user2, instance.modified_by)
                    self.assertEqual(timezone.now().date(), instance.modified_date)
