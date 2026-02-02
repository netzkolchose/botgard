from .base import *

class TestLabelsCSV(TestBase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def test_csv_label_single_garden(self):
        self.login("User1")

        label_model = LabelDefinition.objects.get(id_name="A2")

        self.assert_table(
            label_model,
            "garden", BotanicGarden.objects.get(name="Garden 1"),
            [
                ["Address 1", "Address 2", "Address 3", "Nothing", "Address 4"],
                ["Line 1", "Line 2", "Line 3", "----", "Line 4"],
            ],
        )

        self.assert_table(
            label_model,
            "garden", BotanicGarden.objects.get(name="Garden 2"),
            [
                ["Address 1", "Address 2", "Address 3", "Nothing", "Address 4"],
                ["Linä 1", "Line,2", "Line\\n'3", "----", "Line\"4"],
            ]
        )

    def test_csv_label_single_individual(self):
        self.login("User1")

        label_model = LabelDefinition.objects.get(id_name="I3")

        self.assert_table(
            label_model,
            "individual", Individual.objects.get(accession_number=1000),
            [
                ["IPEN", "Species"],
                ["AU-0-GARD1-1000", "Genus 1 Species 1 Baill."],
            ],
        )

    def test_csv_label_mass_action_garden(self):
        self.login("User1")

        label_model = LabelDefinition.objects.get(id_name="A2")

        self.assert_table(
            label_model,
            "garden",
            [
                BotanicGarden.objects.get(name="Garden 1"),
                BotanicGarden.objects.get(name="Garden 2"),
            ],
            [
                ["Address 1", "Address 2", "Address 3", "Nothing", "Address 4"],
                ["Line 1", "Line 2", "Line 3", "----", "Line 4"],
                ["Linä 1", "Line,2", "Line\\n'3", "----", "Line\"4"],
            ]
        )

    def test_csv_label_mass_action_individual(self):
        self.login("User1")

        label_model = LabelDefinition.objects.get(id_name="I3")

        self.assert_table(
            label_model,
            "individual",
            [
                Individual.objects.get(accession_number=1000),
                Individual.objects.get(accession_number=1001),
            ],
            [
                ["IPEN", "Species"],
                ["AU-0-GARD1-1000", "Genus 1 Species 1 Baill."],
                ["IT-0-GARD2-1001", "Genus 1 Species 2 A. Cunn."],
            ],
            expect_unchecked_nomenclature=True,
        )

    def test_csv_label_mass_action_specimen(self):
        self.login("User1")

        label_model = LabelDefinition.objects.get(id_name="S2")

        self.assert_table(
            label_model,
            "herbarium_specimen",
            [
                HerbariumSpecimen.objects.get(individual__accession_number=1002),
                HerbariumSpecimen.objects.get(individual__accession_number=1003),
            ],
            [
                ["Herbarium", "IPEN", "Collector"],
                ["Herbarium1", "ES-0-GARD2-1003", "User2"],
                ["Herbarium1", "CZ-0-GARD1-1002", "User1"],
            ],
            expect_unchecked_nomenclature=True,
        )

    def assert_table(
            self, label_model: LabelDefinition, object_type: str, object_model, expected_lines: List[List[str]],
            expect_unchecked_nomenclature: bool = False,
    ):
        self.assert_csv(label_model, object_type, object_model, expected_lines, expect_unchecked_nomenclature)
        self.assert_xls(label_model, object_type, object_model, expected_lines, expect_unchecked_nomenclature)

    def assert_csv(
            self, label_model: LabelDefinition, object_type: str, object_model, expected_lines: List[List[str]],
            expect_unchecked_nomenclature: bool = False,
    ):
        response = self.get_label_response(
            label_model, object_type, object_model, "csv",
            expect_unchecked_nomenclature=expect_unchecked_nomenclature,
        )
        fp = StringIO(response.content.decode("utf-8"))
        try:
            lines = list(csv.reader(fp))
            self.assertEqual(len(expected_lines), len(lines), f"expected {len(expected_lines)} table lines")
            self.assertEqual(expected_lines, lines)
        except Exception:
            fp.seek(0)
            print(f"RENDERED RESPONSE:\n{fp.read()}")
            raise

    def assert_xls(
            self, label_model: LabelDefinition, object_type: str, object_model, expected_lines: List[List[str]],
            expect_unchecked_nomenclature: bool = False,
    ):
        response = self.get_label_response(
            label_model, object_type, object_model, "xls",
            expect_unchecked_nomenclature=expect_unchecked_nomenclature,
        )

        try:
            book = xlrd.open_workbook(file_contents=response.content, encoding_override="utf-8")
            sheet = book.sheet_by_index(0)
            lines = [
                [v.value for v in row]
                for row in sheet.get_rows()
            ]
            self.assertEqual(len(expected_lines), len(lines), f"expected {len(expected_lines)} table lines")
            self.assertEqual(expected_lines, lines)
        except Exception:
            print("RENDERED RESPONSE:")
            print(response.content)
            raise
