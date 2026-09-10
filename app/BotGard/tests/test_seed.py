from .base import *

class TestSeed(TestBase):

    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser("User1", password="the-secret")
        project = Project.objects.create(title="Project 1")
        department = Department.objects.create(
            territory=Territory.objects.create(code="T1", name="Territory 1"),
            code="D1",
            name="Department 1",
        )
        literature = Literature.objects.create(title="Literature 1")
        species = Species.objects.create(
            species="Species 1",
            family=Family.objects.create(
                family="Family 1",
                genus="Genus 1",
            )
        )
        garden = BotanicGarden.objects.create(
            name="Garden 1",
            code="G1",
        )
        cls.indi = Individual.objects.create(
            import_reference="IR1",
            ipen_country="au",
            ipen_transfer_restricted="1",
            ipen_garden_code=garden,
            ipen_accession_number="1234",
            accession_number="5678",
            accession_extension="20",
            species=species,
            order_number="10001",
            found_text="Himalaya",
            found_country="in",
            collector_date="2001-01-01",
            collector_name="Bob",
            collector_number="C123",
            comment="Yeah!",
            species_checked_date="2002-03-04",
            species_checked_by="Conny",
            seed_available=True,
            seed_in_stock=True,
            came_as_species="Some spec.",
            came_in_as="PT",
            external_order_number="765",
            gender="W",
            literature=literature,
            source=garden,
            source_date="2010-02-03",
            sowing_number="5566",
            species_comment="Determination by LLM, sorry!",
            status="test",
        )
        cls.indi.projects.add(project)
        Outplanting.objects.create(
            individual=cls.indi,
            department=department,
            date="1995-01-01",
            seeded_date="1994-01-01",
            plant_died="2010-03-04",
            comment="It just died",
            location="SRID=4326;POINT (9.860539005517104 53.56239160512062)",
        )
        cls.prop1 = CustomProperty.objects.create_for_model(model=Individual, name="prop1", type="text")
        cls.indi.custom_values_text.add(PropertyValueText.objects.create(property=cls.prop1, value="custom!"))

    def test_individual_and_seed_changeform_equal(self):
        self.login("User1")

        cf = self.get_changeform("individuals", "individual", self.indi.pk)
        expected_values = {
            f.name: f.value
            for f in cf.fields
            if f.name != "csrfmiddlewaretoken"
               and not f.name.startswith("_")
               and not "herbarium_specimens" in f.name
               and not "outplanting_set" in f.name
               and not "plantimage_set" in f.name
        }
        # pprint.pprint(expected_values)
        self.assertIn(f"custom-property-{self.prop1.pk}", expected_values)

        cf2 = self.get_changeform("individuals", "seed", self.indi.pk)
        values = {
            f.name: f.value
            for f in cf2.fields
        }
        for key, expected_value in expected_values.items():
            self.assertIn(key, values, f"Field '{key}' is missing in seed changeform")
            self.assertEqual(expected_value, values[key])
