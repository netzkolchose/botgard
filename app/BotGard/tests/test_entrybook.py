from .base import *

class TestEntryBook(TestBase):

    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser("User1", password="the-secret")
        Project.objects.create(title="Project 1")
        Project.objects.create(title="Project 2")
        Project.objects.create(title="Project 3")
        Department.objects.create(
            territory=Territory.objects.create(code="T1", name="Territory 1"),
            code="D1",
            name="Department 1",
        )
        Literature.objects.create(title="Literature 1")

    def test_entry_has_same_fields(self):
        self.login("User1")

        cf = self.get_changeform("individuals", "individual")
        expected_field_names = sorted([
            f.name for f in cf.fields
            if not f.name.startswith("initial-")
                and not f.name.startswith("plantimage_")
                and not f.name.startswith("outplanting_")
                and not f.name.startswith("herbarium_specimens")
                and not "__prefix__" in f.name
        ])
        # pprint.pprint(expected_field_names)

        cf = self.get_changeform("entrybook", "entry")
        field_names = sorted([
            f.name for f in cf.fields
            if not f.name.startswith("initial-")
        ])
        # pprint.pprint(field_names)
        extra_fields = ["department", "bed_out_date", "seeded_date"]
        self.assertEqual(sorted(expected_field_names + extra_fields), field_names)

    def test_entry_save_as_individual(self):
        self.login("User1")

        expected_values = {
            'accession_extension': "20",
            'accession_number': "123",
            'bed_out_date': "2000-01-01",
            'came_as_species': "some spec.",
            'came_in_as': "PT",
            'collector_date': "2001-02-03",
            'collector_name': "Boris",
            'collector_number': "55",
            'comment': "Nothing to say",
            'department': str(Department.objects.get(code="D1").pk),
            'external_order_number': "8765",
            'found_country': "AD (Andorra, Principality of)",
            'found_text': "below a brick",
            'gender': "W",
            'import_reference': "987",
            'ipen_accession_number': "98765",
            'ipen_country': "CZ (Czech Republic)",
            'ipen_garden_code': "abc",
            'ipen_transfer_restricted': "1",
            'literature': '"Literature 1"',
            'order_number': "666",
            'projects': str(Project.objects.get(title="Project 3").pk),
            'seed_available': True,
            'seed_in_stock': True,
            'seeded_date': "2345-06-07",
            'source': "xx",
            'source_date': "1980-01-01",
            'sowing_number': "12345",
            'species': "some other spec.",
            'species_checked_by': "me",
            'species_checked_date': "2020-01-01",
            'species_comment': "not checked toroughly",
            'status': "whatever",
        }
        cf = self.get_changeform("entrybook", "entry")

        # first make sure we did not forget a new field
        field_names = sorted([
            f.name for f in cf.fields
            if not f.hidden
                and not f.name.startswith("_")
        ])
        self.assertEqual(set(expected_values.keys()), set(field_names))

        # save Entry
        cf.save(expected_values)
        # see that everything was saved and reload to Entry changeform
        cf.assert_data(expected_values)

        # click save-as-individual
        cf.save_as_individual()

        # check that all values have been copied to "add Individual" changeform
        values = {
            f.name: f.value
            for f in cf.fields
        }
        #pprint.pprint(values)
        for key, expected_value in expected_values.items():
            if key in ("department", "bed_out_date", "seeded_date"):
                continue
            self.assertEqual(expected_value, values[key])
        # also check that value have been put into OutplantingInline

        self.assertEqual(expected_values["department"], values["outplanting_set-0-department"])
        self.assertEqual(expected_values["bed_out_date"], values["outplanting_set-0-date"])
        self.assertEqual(expected_values["seeded_date"], values["outplanting_set-0-seeded_date"])

        # ---- test that OutplantingInline is hidden when no department was selected ----

        expected_values.pop("department")
        expected_values["accession_number"] = expected_values["ipen_accession_number"] = "new123"
        expected_values["order_number"] = "new456"

        cf = self.get_changeform("entrybook", "entry")
        cf.save(expected_values)
        cf.save_as_individual()
        values = {
            f.name: f.value
            for f in cf.fields
        }
        self.assertNotIn("outplanting_set-0-department", values.keys())
