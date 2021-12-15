from django.test import TestCase


from individuals.admin import get_seed_order_ids


class TestStuff(TestCase):

    def test_seed_id_extract(self):
        self.assertEqual(
            ["1001", "1002"],
            get_seed_order_ids("1001, 1002")
        )
        self.assertEqual(
            ["1001", "1002", "66", "42"],
            get_seed_order_ids("1001\n1002, 66 and 42.")
        )
