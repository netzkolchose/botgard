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

    def create_individuals(self, count: int):
        """
        Helper function, creates exactly <count> individuals in the database.
        Accession number starts at 1000
        Every 2nd has `seed_available==True`
        Every 3rd has `seed_in_stock==True`
        """
        demo_indi = Individual.objects.all().first()
        demo_indi = {
            field.name: getattr(demo_indi, field.name)
            for field in demo_indi._meta.fields
            if not (field.name == "id" or field.name.endswith("_generated"))
        }
        # pprint.pprint(demo_indi)
        Individual.objects.all().delete()

        for i in range(300):
            Individual.objects.create(**{
                **demo_indi,
                "accession_number": 1000 + i,
                "ipen_accession_number": 1000 + i,
                "seed_available": i % 2 == 0,
                "seed_in_stock": i % 3 == 0,
                "order_number": i,
            })

    def test_damn_multipart_encoding_problem(self):
        """
        Just to make sure that django behaves as documented when posting
        multipart form data with multiple values of the same name:
        https://docs.djangoproject.com/en/5.2/topics/testing/tools/#django.test.Client.post

        Doing this because of problems with multiple _selected_action in tests.base.ChangeListForm.

        **UPDATE**: Found the thing: don't put a QueryDict in the client.post() data,
            it only yields the LAST entry of a list value. You can construct the params
            with QueryDict but then `post("url", dict(query_dict))`
        """
        from django.test.client import encode_multipart, RequestFactory
        data = QueryDict(mutable=True)
        data["value"] = "1"
        data["_selected_action"] = ["2", "3"]

        encoded = encode_multipart("BoUnDaRy", data).decode()
        self.assertEqual(
            '--BoUnDaRy\r\nContent-Disposition: form-data; name="value"\r\n\r\n1\r\n--BoUnDaRy\r\nContent-Disposition: form-data; name="_selected_action"\r\n\r\n2\r\n--BoUnDaRy\r\nContent-Disposition: form-data; name="_selected_action"\r\n\r\n3\r\n--BoUnDaRy--\r\n',
            encoded
        )

        rf = RequestFactory()
        request = rf.post("/some/path", data)
        self.assertEqual(
            b'--BoUnDaRyStRiNg\r\nContent-Disposition: form-data; name="value"\r\n\r\n1\r\n--BoUnDaRyStRiNg\r\nContent-Disposition: form-data; name="_selected_action"\r\n\r\n2\r\n--BoUnDaRyStRiNg\r\nContent-Disposition: form-data; name="_selected_action"\r\n\r\n3\r\n--BoUnDaRyStRiNg--\r\n',
            request.body
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
        """
        Select two of the three seeds to be "in stock" in the changelist and save

        This is more like a django admin tests, not really our own functionallity that's tested
        """
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

    #@log_requests
    def test_seed_catalog_changelist_add_to_catalog(self):
        # 300 individuals/seeds
        self.create_individuals(300)
        # current catalog is empty
        self.assertEqual(0, SeedCatalog.objects.latest_editable_catalog().seed.all().count())

        self.login("User1")
        cl = self.get_changelist("individuals", "seed")
        # just 100 per page
        self.assertEqual(100, len(cl.rows))
        self.assertEqual(3, cl.num_pages)

        # filter changelist
        cl.update_filters({
            "seed_available__exact": "1",   # every second
            "seed_in_stock__exact": "1",    # every third
        })
        # 300 // 2 // 3
        self.assertEqual(50, len(cl.rows))

        # add filtered seeds to catalog
        cl.run_action(
            "add_seeds_to_current_catalog",
            rows=(0, 50),
        )
        self.assertEqual(50, len(cl.rows))  # filter is still present
        # added to catalog?
        self.assertEqual(50, SeedCatalog.objects.latest_editable_catalog().seed.all().count())

        # -- check is-in-latest-catalog filter --

        cl = self.get_changelist("individuals", "seed")
        cl.update_filters({"seedcatalog": "yes"})
        self.assertEqual(50, len(cl.rows))

        # combine filters
        cl.update_filters({"seedcatalog": "yes", "accession_number__icontains": "100"})
        self.assertEqual(["1000", "1006"], [row["accession_number"] for row in cl.rows])

        cl.run_action(
            "remove_seeds_from_current_catalog",
            rows=(0, 2),
        )
        self.assertEqual(0, len(cl.rows))

        cl.update_filters({"seedcatalog": "yes"})
        self.assertEqual(48, len(cl.rows))
