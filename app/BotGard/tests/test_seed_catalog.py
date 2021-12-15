import re

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.admindocs.views import simplify_regex
from django.utils import timezone
from django.contrib.auth import get_user_model

from individuals.models import Seed
from seedcatalog.models import SeedCatalog

from .fixtures import create_test_fixtures


class TestSeedCatalog(TestCase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

        UserModel = get_user_model()
        cls.admin = UserModel.objects.create_user(
            username="admin", password="pass",
            is_staff=True, is_superuser=True,
        )

    def test_seed_catalog(self):
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
        self.assertIn(".pdf", pdf_link)
