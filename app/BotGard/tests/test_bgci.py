import pprint

from .base import *
from botman.utils import fuzzy_find_bgci_garden


class TestBGCI(TestBase):

    @classmethod
    def setUpTestData(cls):
        UserModel.objects.create_superuser(
            username="User1", password="the-secret"
        )
        user = UserModel.objects.create_user(
            username="User2", password="the-secret", is_staff=True,
        )
        group = create_permission_group("gardens", {
            "botman.botanicgarden": {"add", "view", "change"},
            "botman.bgcigarden": {"view"},
        })
        user.groups.add(group)

        user = UserModel.objects.create_user(
            username="User3", password="the-secret", is_staff=True,
        )
        group = create_permission_group("gardens-readonly", {
            "botman.botanicgarden": {"view"},
            "botman.bgcigarden": {"view"},
        })
        user.groups.add(group)

    def create_gardens(self, *names: str) -> List[BotanicGarden]:
        gardens = []
        for name in names:
            gardens.append(BotanicGarden.objects.create(
                name=name,
                code=None,
                number=BotanicGarden.objects.count() + 1,
            ))
        return gardens

    def create_bgci_gardens(self, *names_or_names_and_cities: Union[str, Tuple[str, str]]) -> List[BGCIGarden]:
        gardens = []
        for name_or_name_and_city in names_or_names_and_cities:
            name = name_or_name_and_city
            city = None
            if isinstance(name, (list, tuple)):
                name, city = name_or_name_and_city
            gardens.append(BGCIGarden.objects.create(
                name=name,
                city=city,
                ipen_code=None,
                bgci_id=BGCIGarden.objects.count() + 1,
                type="garden",
                bgci_data={},
            ))
        return gardens

    def assert_equal(self, expected: List, actual: List):
        self.assertEqual(
            expected,
            actual,
            f"\nexpected:\n{pprint.pformat(expected,)}\ngot:\n{pprint.pformat(actual)}"
        )

    def test_bgci_fuzzy_search(self):
        UD, SU, GD, GS = self.create_bgci_gardens(
            "University of Dobbstown",
            "Shady University",
            "Garden of Dobbstown",
            ("Garden in the Shades", "Dobbshaven"),
        )
        with self.subTest("1 term"):
            self.assert_equal(
                [UD, GS, GD, SU],
                fuzzy_find_bgci_garden("University of Dobbstown"),
            )
        with self.subTest("2 terms"):
            self.assert_equal(
                [
                    [UD, GS, GD, SU],
                    [GS, SU, GD, UD],
                ],
                fuzzy_find_bgci_garden("University of Dobbstown", "Shady"),
            )

    def test_bgci_fuzzy_search_scores(self):
        ABC, AB, BC, D = self.create_bgci_gardens(
            ("ABC", "D"),
            "AB",
            "BC",
            "D",
        )
        with self.subTest("1 term"):
            self.assert_equal(
                [(ABC, 200), (AB, 180), (BC, 180), (D, 0)],
                fuzzy_find_bgci_garden("ABC", with_scores=True),
            )
        with self.subTest("3 terms"):
            self.assert_equal(
                [
                    [(ABC, 200), (AB, 180), (BC, 180), (D, 0)],
                    [(ABC, 200), (D, 200), (AB, 0), (BC, 0)],
                ],
                fuzzy_find_bgci_garden("ABC", "D", with_scores=True),
            )

    def test_map_bgci_permissions(self):
        self.create_gardens("Garden1", "Garden2")
        self.create_bgci_gardens("Garden1", "Garden2")

        for username, expect_access in (
            ("User1", True),
            ("User2", True),
            ("User3", False),
        ):
            with self.subTest(username):
                self.login(username)

                response = self.client.get(reverse("botman:map_bgci"))
                if expect_access:
                    self.assertEqual(200, response.status_code)
                else:
                    self.assertEqual(302, response.status_code)
                    self.assertIn("no_permission", response.headers.get("Location") or "")

    def test_map_bgci_admin_permissions(self):
        """
        Check that the map-bgci-gardens action button is only visible to users with matching permissions
        """
        self.create_gardens("Garden1", "Garden2")
        self.create_bgci_gardens("Garden1", "Garden2")

        for username, expect_access in (
                ("User1", True),
                ("User2", True),
                ("User3", False),
        ):
            with self.subTest(username):
                self.login(username)
                try:
                    response = self.client.get(reverse("admin:botman_botanicgarden_changelist"))
                    self.assertEqual(200, response.status_code)
                    if expect_access:
                        self.assertIn(reverse("botman:map_bgci").encode(), response.content)
                    else:
                        self.assertNotIn(reverse("botman:map_bgci").encode(), response.content)

                finally:
                    self.client.logout()