from .base import *

class TestAudit(TestBase):

    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        fixtures.create_test_fixtures()

    def test_individual_species_audit(self):
        self.login("User1")

        indi = Individual.objects.get(accession_number=1000)
        cf = self.get_changeform("individuals", "individual", indi.pk)
        # make sure, the audit widget is not displayed
        self.assertIsNone(cf.soup.find("div", {"class": "species-audit-widget"}))
        cf.save()

        indi.refresh_from_db()
        self.assertIsNone(indi.species_audit)

        # -- User1 changes species --
        cf.save({"species": Species.objects.get(species="Species 2").full_name_generated})
        self.assertIsNotNone(cf.soup.find("div", {"class": "species-audit-widget"}))

        indi.refresh_from_db()
        # pprint.pprint(indi.species_audit)
        today = timezone.now().date().isoformat()
        self.assertEqual(
            [
                {
                    'date': today,
                    'species': 'Genus 1 Species 1 Baill.',
                    'species_pk': Species.objects.get(species="Species 1").pk,
                    'user': None,
                    'user_pk': None,
                    'literature': None,
                    'literature_pk': None,
                },
                {
                    'date': today,
                    'species': 'Genus 1 Species 2 A. Cunn.',
                    'species_pk': Species.objects.get(species="Species 2").pk,
                    'user': 'User1',
                    'user_pk': User.objects.get(username="User1").pk,
                    'literature': None,
                    'literature_pk': None,
                }
            ],
            indi.species_audit
        )

        # -- User3 changes species back --
        self.login("User3")
        cf = self.get_changeform("individuals", "individual", indi.pk)
        cf.save({
            "species": Species.objects.get(species="Species 1").full_name_generated,
            "literature": Literature.objects.get(title="Title 1").full_name_generated,
        })

        indi.refresh_from_db()
        self.assertEqual(
            [
                {
                    'date': today,
                    'species': 'Genus 1 Species 1 Baill.',
                    'species_pk': Species.objects.get(species="Species 1").pk,
                    'user': None,
                    'user_pk': None,
                    'literature': None,
                    'literature_pk': None,
                },
                {
                    'date': today,
                    'species': 'Genus 1 Species 2 A. Cunn.',
                    'species_pk': Species.objects.get(species="Species 2").pk,
                    'user': 'User1',
                    'user_pk': User.objects.get(username="User1").pk,
                    'literature': None,
                    'literature_pk': None,
                },
                {
                    'date': today,
                    'species': 'Genus 1 Species 1 Baill.',
                    'species_pk': Species.objects.get(species="Species 1").pk,
                    'user': 'User3',
                    'user_pk': User.objects.get(username="User3").pk,
                    'literature': "1984. \"Title 1\"",
                    'literature_pk': Literature.objects.get(title="Title 1").pk,
                },
            ],
            indi.species_audit
        )

        # -- User2 changes species but provides different username and date --
        # ALSO: check that seed admin also adds to the audit
        cf = self.get_changeform("individuals", "seed", indi.pk)
        cf.save({
            "species": Species.objects.get(species="Species 3").full_name_generated,
            "species_checked_by": "Bob Dobbs",
            "species_checked_date": "2030-01-01",
            "literature": Literature.objects.get(title="Title 2").full_name_generated,
        })

        expected_species_audit = [
            {
                'date': today,
                'species': 'Genus 1 Species 1 Baill.',
                'species_pk': Species.objects.get(species="Species 1").pk,
                'user': None,
                'user_pk': None,
                'literature': None,
                'literature_pk': None,
            },
            {
                'date': today,
                'species': 'Genus 1 Species 2 A. Cunn.',
                'species_pk': Species.objects.get(species="Species 2").pk,
                'user': 'User1',
                'user_pk': User.objects.get(username="User1").pk,
                'literature': None,
                'literature_pk': None,
            },
            {
                'date': today,
                'species': 'Genus 1 Species 1 Baill.',
                'species_pk': Species.objects.get(species="Species 1").pk,
                'user': 'User3',
                'user_pk': User.objects.get(username="User3").pk,
                'literature': "1984. \"Title 1\"",
                'literature_pk': Literature.objects.get(title="Title 1").pk,
            },
            {
                'date': "2030-01-01",
                'species': 'Genus 2 Species 3 C. Morren',
                'species_pk': Species.objects.get(species="Species 3").pk,
                'user': 'Bob Dobbs',
                'user_pk': None,
                'literature': '"Title 2" Plants of the Moon, vol. 23',
                'literature_pk': Literature.objects.get(title="Title 2").pk,
            }
        ]
        indi.refresh_from_db()
        self.assertEqual(
            expected_species_audit,
            indi.species_audit
        )

        # -- save without changes --
        cf = self.get_changeform("individuals", "individual", indi.pk)
        cf.save()
        indi.refresh_from_db()
        self.assertEqual(
            expected_species_audit,
            indi.species_audit
        )

        # -- also check widget rendering --
        cf = self.get_changeform("individuals", "individual", indi.pk)
        div = cf.soup.find("div", {"class": "species-audit-widget"})
        self.assertIsNotNone(div, "Missing SpeciesAuditWidget in chnageform")
        rows = []
        for row in div.find("tbody").find_all("tr"):
            rows.append([
                td.find("input").attrs["value"]
                for td in row.find_all("td")
            ])
        #pprint.pprint(rows)
        self.assertEqual(
            [
                ['Genus 1 Species 1 Baill.', '-', today, '-'],
                ['Genus 1 Species 2 A. Cunn.', 'User1', today, '-'],
                ['Genus 1 Species 1 Baill.', 'User3', today, '1984. "Title 1"'],
                ['Genus 2 Species 3 C. Morren', 'Bob Dobbs', '2030-01-01', '"Title 2" Plants of the Moon, vol. 23'],
            ],
            rows
        )