from .base import *

class TestCsvExport(TestBase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def test_csv_export(self):
        self.login("User1")

        prop1: CustomProperty = CustomProperty.objects.get(name="individual_comment")
        prop1.set_value_for_model(Individual.objects.get(accession_number="1002"), "Two tree")

        cl = self.get_changelist("individuals", "individual")
        cl.set_columns([
            "accession_number", "species_link_decorator",
            f"custom_property_decorator_{prop1.pk}"
        ])

        cl.assert_csv_export(
            [
                ['accession #', 'species', 'individual_comment'],
                ['1000', 'Genus 1 Species 1 Baill.', 'A tree'],
                ['1001', 'Genus 1 Species 2 A. Cunn.', '-'],
                ['1002', 'Genus 2 Species 3 C. Morren', 'Two tree'],
                ['1003', 'Genus 2 Species 3 C. Morren', '-']
            ],
        )
        cl.assert_csv_export(
            [
                ['accession #', 'species', 'individual_comment'],
                ['1000', 'Genus 1 Species 1 Baill.', 'A tree'],
            ],
            override_params={"accession_number__icontains": "000"},
        )
        cl.assert_csv_export(
            [
                ['accession #', 'species', 'individual_comment'],
                ['1000', 'Genus 1 Species 1 Baill.', 'A tree'],
                ['1002', 'Genus 2 Species 3 C. Morren', 'Two tree'],
            ],
            override_params={f"custom_property_{prop1.pk}": "tree"},
        )