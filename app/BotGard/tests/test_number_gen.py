import datetime
import random
from typing import Union

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.admindocs.views import simplify_regex
from django.conf import settings

from botman.models import BotanicGarden
from species.models import Family, Species
from individuals.models import Department, Territory, Individual, Outplanting
from entrybook.models import Entry
from labels.models import LabelDefinition
from tickets.models import BasicTicket, LaserGravurTicket
from individuals import numbers
from config_app.models import KeyValue

from .fixtures import create_test_fixtures


class TestNumberGenerator(TestCase):

    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

    def create_entry(
            self,
            accession_number: Union[int, str],
            order_number: Union[int, str, None] = None,
    ):
        if order_number is None:
            order_number = accession_number

        return Entry.objects.create(
            accession_number=accession_number,
            ipen_accession_number=accession_number,
            order_number=order_number,
            seed_available=False,
            seed_in_stock=False,
        )

    def create_individual(
            self,
            accession_number: Union[int, str],
            order_number: Union[int, str, None] = None,
    ):
        if order_number is None:
            order_number = accession_number
        species = random.choice(list(Species.objects.all()))
        garden = random.choice(list(BotanicGarden.objects.all()))

        return Individual.objects.create(
            accession_number=accession_number,
            accession_extension="",
            species=species,
            species_checked_by="",
            came_as_species="",
            ipen_country="CZ",
            ipen_transfer_restricted="0",
            ipen_garden_code=garden,
            ipen_accession_number=accession_number,
            source=garden,
            source_date=None,
            came_in_as="",
            found_country="GP",
            found_text="",
            collector_name="",
            collector_number="",
            collector_date=None,
            gender="",
            comment="",
            seed_available=True,
            order_number=order_number,
            seed_collector_date=None,
            seed_in_stock=True,
            sowing_number="",
        )

    def test_number_gen_random(self):
        KeyValue.objects.create(
            type="j",
            key="accession_generation",
            value_json={
                "method": "random_range",
                "min": 2000, "max": 2009,
            },
        )
        KeyValue.objects.create(
            type="j",
            key="order_number_generation",
            value_json={
                "method": "random_range",
                "min": 3000, "max": 3009,
            },
        )

        # create some text accession numbers as well
        self.create_individual("test1", "test1")
        self.create_individual("XY-1992", "XY-1992")

        acc_nums = []
        order_nums = []
        for i in range(10):
            acc_num = numbers.get_new_accession_number()
            order_num = numbers.get_new_order_number()

            if i % 2 == 0:
                self.create_individual(
                    accession_number=acc_num,
                    order_number=order_num,
                )
            else:
                self.create_entry(
                    accession_number=acc_num,
                    order_number=order_num,
                )

            if acc_num in acc_nums:
                raise AssertionError(f"Generated duplicate accession number '{acc_num}'")
            if order_num in order_nums:
                raise AssertionError(f"Generated duplicate order number '{acc_num}'")

            acc_nums.append(acc_num)
            order_nums.append(order_num)

        # make sure we generated all possible numbers

        self.assertEqual(
            list(range(2000, 2010)),
            sorted(acc_nums)
        )

        self.assertEqual(
            list(range(3000, 3010)),
            sorted(order_nums)
        )

        # no numbers left in defined space

        with self.assertRaises(RuntimeError):
            numbers.get_new_accession_number()

        with self.assertRaises(RuntimeError):
            numbers.get_new_order_number()

    def test_number_gen_incremental(self):
        KeyValue.objects.create(
            type="j",
            key="accession_generation",
            value_json={
                "method": "incremental",
                "min": 2000,
            },
        )
        KeyValue.objects.create(
            type="j",
            key="order_number_generation",
            value_json={
                "method": "incremental",
                "min": 3000,
            },
        )

        self.assertEqual(2000, numbers.get_new_accession_number())
        self.assertEqual(3000, numbers.get_new_order_number())

        self.create_individual(2005, 3008)
        # create some text accession numbers as well
        self.create_individual("test1", "test1")
        self.create_individual("XY-1992", "XY-1992")

        self.assertEqual(2006, numbers.get_new_accession_number())
        self.assertEqual(3009, numbers.get_new_order_number())

        self.create_entry(2010, 3012)

        self.assertEqual(2011, numbers.get_new_accession_number())
        self.assertEqual(3013, numbers.get_new_order_number())

    def test_number_gen_incremental_tight(self):
        KeyValue.objects.create(
            type="j",
            key="accession_generation",
            value_json={
                "method": "incremental_tight",
                "min": 2000,
            },
        )
        KeyValue.objects.create(
            type="j",
            key="order_number_generation",
            value_json={
                "method": "incremental_tight",
                "min": 3000,
            },
        )

        # take min value if no collision yet
        self.assertEqual(2000, numbers.get_new_accession_number())
        self.assertEqual(3000, numbers.get_new_order_number())

        self.create_individual(2002, 3003)
        # create some text accession numbers as well
        self.create_individual("test1", "test1")
        self.create_individual("XY-1992", "XY-1992")

        # they are still free
        self.assertEqual(2000, numbers.get_new_accession_number())
        self.assertEqual(3000, numbers.get_new_order_number())

        self.create_individual(2000, 3000)
        self.create_entry(2001, 3002)
        self.create_individual("ABC", "ABC")
        self.create_entry("XY-1998", "XY-1998")

        # it's fitting tight!
        self.assertEqual(2003, numbers.get_new_accession_number())
        self.assertEqual(3001, numbers.get_new_order_number())

        self.create_individual(2004, 3001)
        self.create_entry(2005, 3004)

        # it's still fitting tight!
        self.assertEqual(2003, numbers.get_new_accession_number())
        self.assertEqual(3005, numbers.get_new_order_number())

    def test_number_gen_empty(self):
        KeyValue.objects.create(
            type="j",
            key="accession_generation",
            value_json={
                "method": "empty",
            },
        )
        KeyValue.objects.create(
            type="j",
            key="order_number_generation",
            value_json={
                "method": "empty",
            },
        )

        self.assertEqual("", numbers.get_new_accession_number())
        self.assertEqual("", numbers.get_new_order_number())

    def test_number_gen_year_id(self):
        KeyValue.objects.create(
            type="j",
            key="accession_generation",
            value_json={
                "method": "year_id",
                "min": 1,
            },
        )
        KeyValue.objects.create(
            type="j",
            key="order_number_generation",
            value_json={
                "method": "year_id",
                "min": 1,
            },
        )
        year = datetime.date.today().year

        # take min value if no collision yet
        self.assertEqual(f"{year}-1", numbers.get_new_accession_number())
        self.assertEqual(f"{year}-1", numbers.get_new_order_number())

        self.create_individual(f"{year}-1")
        # create some other accession numbers as well
        # they should not interfere with the year_id counter
        self.create_individual("test1")
        self.create_individual("XY-1992")
        self.create_individual(f"{year-1}-23")

        self.assertEqual(f"{year}-2", numbers.get_new_accession_number())
        self.assertEqual(f"{year}-2", numbers.get_new_order_number())

        self.create_individual(f"{year}-3")
        self.create_entry(f"{year}-4", f"{year}-5")
        self.create_individual("ABC")
        self.create_entry("XY-1998")

        self.assertEqual(f"{year}-5", numbers.get_new_accession_number())
        self.assertEqual(f"{year}-6", numbers.get_new_order_number())

        # check that natural sorting is used
        self.create_individual(f"{year}-10")

        if settings.IS_POSTGRES:
            self.assertEqual(f"{year}-11", numbers.get_new_accession_number())
            self.assertEqual(f"{year}-11", numbers.get_new_order_number())
        else:
            # without natural sort we have 1, 10, 2, 3, 4
            self.assertEqual(f"{year}-5", numbers.get_new_accession_number())
            self.assertEqual(f"{year}-6", numbers.get_new_order_number())
