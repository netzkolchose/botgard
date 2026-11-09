from .base import *

class TestLabelsActions(TestBase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def test_label_actions(self):
        self.login(username="User1")

        for label_type, _ in LABEL_TYPE_CHOICES:
            with self.subTest(label_type=label_type):
                label_qset = LabelDefinition.objects.filter(type=label_type)
                self.assertTrue(label_qset.exists(), f"No {label_type} label in test fixtures")

                Model = label_qset.first().model_class

                cl = self.get_changelist(Model._meta.app_label, Model._meta.model_name)

                for label in label_qset:
                    formats = []
                    if label.format == "csv":
                        formats = ["csv", "xls"]
                    elif label.format == "html":
                        formats = ["html", "pdf"]

                    def _iter_responses():
                        if not formats:
                            yield None, cl.label_action(label.id_name)
                        else:
                            for format in formats:
                                yield format, cl.label_action(label.id_name, format)

                    for format, response in _iter_responses():
                        if format:
                            if format == "xls":
                                format = "ms-excel"
                            self.assertIn(format, response.headers["content-type"])
