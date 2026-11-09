from .base import *

class TestCsvExport(TestBase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()
        cls.USER_NO_ACCESS = User.objects.create_user(
            username="NoPermission", password=cls.DEFAULT_PASSWORD, is_staff=True,
        )

    def test_csv_export_protected(self):
        self.login("User1")
        cl = self.get_changelist("individuals", "individual")
        self.client.logout()

        cl.get_csv_export(expect_access=False)

        self.login("NoPermission")
        cl.get_csv_export(expect_access=False)

        self.login("User1")
        cl.get_csv_export()

    def test_csv_export_custom_props(self):
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

    def test_csv_export_individual(self):
        self.login("User1")

        prop1: CustomProperty = CustomProperty.objects.get(name="individual_comment")

        indi: Individual = Individual.objects.get(accession_number="1000")
        indi.pk = None
        indi.accession_number = "2000"
        indi.order_number = "2000"
        indi.collector_date = "2020-01-01"
        indi.save()

        cl = self.get_changelist("individuals", "individual")
        #print(cl.get_all_possible_columns())
        cl.set_columns([
            'accession_number', 'found_coordinates_decorator',
            'collector_date', 'etikett_link_decorator',
            'delete_link_decorator', 'departments_decorator', 'etikett_detail_decorator',
            'endangering_decorator', 'has_specimen_generated', 'image_decorator',
            f'custom_property_decorator_{prop1.pk}',
            'is_alive', 'etikett_text_decorator', 'literature', 'locations_decorator',
            'map_decorator', 'modified_date', 'modified_by',
            'nomenclature_checked_decorator', 'projects_decorator',
            'seed_available', 'change_link_decorator', 'source',
            'species_link_decorator', 'territories_decorator'
        ])
        #for row in cl.get_csv_export():
        #    print(row)
        cl.assert_csv_export(
            [
                ['accession #', 'collecting coordinates', 'collection date', 'departments', 'detailed', 'endangering', 'has specimen', 'individual_comment', 'is alive', 'label text', 'literature', 'locations', 'modified at', 'modified by', 'nomenclature checked', 'projects', 'seed available', 'source', 'species', 'territories'],
                ['1000', '-', '-', 'T1-D1', '-', '-', '-', 'A tree', 'X', '-', '-', '-', '-', '-', '-', '-', 'X', '0 (GARD1/Garden 1)', 'Genus 1 Species 1 Baill.', 'T1'],
                ['1001', '-', '-', 'T1-D1', '-', '-', '-', '-', 'X', '-', '1984. "Title 1"', '-', '-', '-', '-', '-', 'X', '1 (GARD2/Garden 2)', 'Genus 1 Species 2 A. Cunn.', 'T1'],
                ['1002', '-', '-', 'T2-D2', '-', '-', 'X', '-', 'X', '-', '"Title 2" Plants of the Moon, vol. 23', '-', '-', '-', '-', '-', 'X', '0 (GARD1/Garden 1)', 'Genus 2 Species 3 C. Morren', 'T2'],
                ['1003', '-', '-', '-', '-', '-', 'X', '-', '-', '-', '-', '-', '-', '-', '-', '-', 'X', '1 (GARD2/Garden 2)', 'Genus 2 Species 3 C. Morren', '-'],
                ['2000', '-', 'Jan. 1, 2020', 'T1-D1', '-', '-', '-', '-', 'X', '-', '-', '-', '-', '-', '-', '-', 'X', '0 (GARD1/Garden 1)', 'Genus 1 Species 1 Baill.', 'T1'],
            ]
        )
