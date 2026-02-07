import pprint

from .base import *


class TestSeedCatalog(TestBase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

        cls.admin = User.objects.create_user(
            username="admin", password="pass",
            is_staff=True, is_superuser=True,
        )

    def test_seed_catalog_rendering(self):
        catalog = SeedCatalog.objects.create(
            release_date=timezone.now(),
            valid_until_date=timezone.now(),
            is_finalized=True,
            copyright_note="netzkolchose.de",
            preface="Our amazing seed catalog",
            notes="Pay two and get three!",
        )
        for seed in Seed.objects.all():
            catalog.seed.add(seed)

        self.assertGreaterEqual(catalog.seed.all().count(), 3)

        self.client.login(username="admin", password="pass")

        response = self.client.get(reverse("seedcatalog:generate", args=(catalog.pk,)), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertNotIn(
            "no_permission",
            response.redirect_chain[0][0],
        )

        catalog.refresh_from_db()

        pdf_link = catalog.pdf_file_decorator()
        self.assertIn(".pdf", pdf_link, f"Debug output: {catalog.debug_output}")

    #@log_requests
    def test_seed_catalog_changelist_save_in_stock(self):
        self.login("User1")
        cl = self.get_changelist("individuals", "seed")
        self.assertGreaterEqual(len(cl.rows), 3)

        rows = [
            cl.get_row(accession_number=accession_number)
            for accession_number in (1000, 1001, 1002)
        ]
        self.assertEqual(
            [True, True, True],
            [r["seed_in_stock"].value for r in rows]
        )

        cl.post({
            "_save": "Save",
            rows[0]["seed_in_stock"].name: False,
            rows[2]["seed_in_stock"].name: False,
        })

        rows = [
            cl.get_row(accession_number=accession_number)
            for accession_number in (1000, 1001, 1002)
        ]
        self.assertEqual(
            [False, True, False],
            [r["seed_in_stock"].value for r in rows]
        )
