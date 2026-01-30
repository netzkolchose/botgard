from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from botman.models import *
from species.models import *
from individuals.models import *
from herbaria.models import *

from .fixtures import create_test_fixtures


class TestModelDependencies(TestCase):
    """
    Test the dependend fields of different models, typicall called ..._generated

    See comment in tools/data_migration.py for all dependencies
    """
    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def test_individual_has_specimen_generated(self):
        """
        Test that Individual.has_specimen_generated is updated when adding or deleting HerbariumSpecimen
        """
        indiA = Individual.objects.get(accession_number=1000)
        indiB = Individual.objects.get(accession_number=1001)
        user = get_user_model().objects.get(username="User1")

        self.assertEqual(False, indiA.has_specimen_generated)
        self.assertEqual(False, indiB.has_specimen_generated)

        herbarium = Herbarium.objects.create(name="Herbarium")

        specimenA1 = HerbariumSpecimen.objects.create(herbarium=herbarium, individual=indiA, collector=user)
        specimenA2 = HerbariumSpecimen.objects.create(herbarium=herbarium, individual=indiA, collector=user, specimen_type="leaves")

        specimenB1 = HerbariumSpecimen.objects.create(herbarium=herbarium, individual=indiB, collector=user)

        indiA.refresh_from_db()
        indiB.refresh_from_db()
        self.assertEqual(True, indiA.has_specimen_generated)
        self.assertEqual(True, indiB.has_specimen_generated)

        specimenA1.delete()
        specimenB1.delete()

        indiA.refresh_from_db()
        indiB.refresh_from_db()
        self.assertEqual(True, indiA.has_specimen_generated)
        self.assertEqual(False, indiB.has_specimen_generated)

        specimenA2.delete()

        indiA.refresh_from_db()
        indiB.refresh_from_db()
        self.assertEqual(False, indiA.has_specimen_generated)
        self.assertEqual(False, indiB.has_specimen_generated)

