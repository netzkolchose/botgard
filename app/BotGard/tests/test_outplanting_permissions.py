import pprint

from .base import *


READ_INDIVIDUAL_PERMISSIONS = {
    'individuals.department': {'view'},
    'individuals.individual': {'view'},
    'individuals.outplanting': {'view'},
    'individuals.seed': {'view'},
    'individuals.territory': {'view'},
    'individuals.': {'view'},
    'species.family': {'view'},
    'species.species': {'view'},
}

CHANGE_INDIVIDUAL_PERMISSIONS = {
    'individuals.department': {'change', 'add'},
    'individuals.individual': {'change', 'add'},
    'individuals.outplanting': {'change', 'add'},
    'individuals.seed': {'change', 'add'},
    'individuals.territory': {'change', 'add'},
    'species.family': {'change', 'add'},
    'species.species': {'change', 'add'},
}

CHANGE_OUTPLANTING_PERMISSIONS = {
    'individuals.outplanting': {'change'},
}

ADD_OUTPLANTING_PERMISSIONS = {
    'individuals.outplanting': {'add'},
}


class TestOutplantingPermissions(TestBase):
    """
    Test to make sure use can change Individual.outplantings
    even though there is only individual-view permission
    """
    @classmethod
    def setUpTestData(cls):
        create_test_fixtures()

        group_read = create_permission_group("read", READ_INDIVIDUAL_PERMISSIONS)
        group_change_indi = create_permission_group("change-indi", CHANGE_INDIVIDUAL_PERMISSIONS)
        group_change_outpl = create_permission_group("change-outpl", CHANGE_OUTPLANTING_PERMISSIONS)
        group_add_outpl = create_permission_group("add-outpl", ADD_OUTPLANTING_PERMISSIONS)

        User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password=cls.DEFAULT_PASSWORD,
        )
        def create_staff(name: str, groups: List[Group]):
            user = User.objects.create_user(
                username=name,
                email=f"{name}@example.com",
                password=cls.DEFAULT_PASSWORD,
                is_staff=True,
            )
            for group in groups:
                user.groups.add(group)
            return user

        cls.user_noread = create_staff("noread", [])
        cls.user_read = create_staff("read", [group_read])
        cls.user_change_indi = create_staff("change-indi", [group_read, group_change_indi])
        cls.user_change_outpl = create_staff("change-outpl", [group_read, group_change_outpl])
        cls.user_add_outpl = create_staff("add-outpl", [group_read, group_change_outpl, group_add_outpl])
        cls.user_only_outpl = create_staff("only-outpl", [group_change_outpl, group_add_outpl])

    def test_noread(self):
        for user in ("noread", "only-outpl"):
            with self.subTest(f"User: {user}"):
                self.login(user)
                indi = Individual.objects.get(accession_number="1000")
                response = self.client.get(reverse("admin:individuals_individual_change", args=(indi.pk,)))
                self.assert_response(response, status=403)
                response = self.client.post(reverse("admin:individuals_individual_change", args=(indi.pk,)))
                self.assert_response(response, status=403)

    def test_read_species(self):
        self.login("read")
        species = Species.objects.get(species="Species 1")
        cf = self.get_changeform("species", "species", pk=species.pk)
        cf.assert_save_button(False)
        # only a few hidden fields (like csrf and ..._set-MAX_FORMS)
        self.assertEqual([], cf.visible_fields())
        cf.assert_save_forbidden()

    def test_read_indi(self):
        self.login("read")
        indi = Individual.objects.get(accession_number="1000")
        cf = self.get_changeform("individuals", "individual", pk=indi.pk)
        cf.assert_save_button(False)
        # only a few hidden fields (like csrf and ..._set-MAX_FORMS)
        self.assertEqual([], cf.visible_fields())
        cf.assert_save_forbidden()

    def test_change_indi(self):
        self.login("change-indi")
        indi = Individual.objects.get(accession_number="1000")
        D2 = Department.objects.get(code="D2")
        cf = self.get_changeform("individuals", "individual", pk=indi.pk)
        cf.assert_save_button()
        cf.save({
            "accession_number": "1234",
            "outplanting_set-0-comment": "Comment1",
            # add outplanting
            "outplanting_set-TOTAL_FORMS": 2,
            "id_outplanting_set-1-id": "",
            "id_outplanting_set-1-individual": str(indi.pk),
            "outplanting_set-1-department": str(D2.pk),
            "outplanting_set-1-date": "2022-01-01",
            "outplanting_set-1-comment": "Comment2",
        })
        indi.refresh_from_db()
        self.assertEqual("1234", indi.accession_number)
        self.assertEqual(
            ["D1", "D2"],
            list(indi.outplanting_set.all().order_by("pk").values_list("department__code", flat=True))
        )
        self.assertEqual(
            ["Comment1", "Comment2"],
            list(indi.outplanting_set.all().order_by("pk").values_list("comment", flat=True))
        )

    def test_change_outpl(self):
        self.login("change-outpl")
        indi = Individual.objects.get(accession_number="1000")
        D1 = Department.objects.get(code="D1")
        D2 = Department.objects.get(code="D2")
        D3 = Department.objects.get(code="D3")
        cf = self.get_changeform("individuals", "individual", pk=indi.pk)
        cf.assert_save_button(True)
        self.assertNotEqual([], cf.visible_fields())
        cf.save({
            "accession_number": "1234",  # won't be saved
            "outplanting_set-0-department": str(D3.pk),
            "outplanting_set-0-comment": "Comment1",
            # add outplanting (which does not work)
            "outplanting_set-TOTAL_FORMS": 2,
            "id_outplanting_set-1-id": "",
            "id_outplanting_set-1-individual": str(indi.pk),
            "outplanting_set-1-department": str(D2.pk),
            "outplanting_set-1-date": "2022-01-01",
            "outplanting_set-1-comment": "Comment2",
        }, expect_fields=False)

        indi.refresh_from_db()
        self.assertEqual("1000", indi.accession_number) # it's unchanged!
        self.assertEqual(
            ["D3"],
            list(indi.outplanting_set.all().order_by("pk").values_list("department__code", flat=True))
        )
        self.assertEqual(
            ["Comment1"],
            list(indi.outplanting_set.all().order_by("pk").values_list("comment", flat=True))
        )
        today = timezone.now().date().isoformat()
        self.assertEqualNice(
            [
                {
                    'date': today,
                    'user': "-",
                    'user_pk': None,
                    'outplantings': [
                        {
                            'pk': indi.outplanting_set.order_by("pk")[0].pk,
                            'department': str(D1),
                            'department_pk': D1.pk,
                            'location': None, 'seeded_date': None, 'date': None,
                            'inventory_date': None,
                            'plant_died': None,
                            'comment': None,
                        }
                    ],
                },
                {
                    'date': today,
                    'user': self.user_change_outpl.username,
                    'user_pk': self.user_change_outpl.pk,
                    'outplantings': [
                        {
                            'pk': indi.outplanting_set.order_by("pk")[0].pk,
                            'date': None,
                            'comment': "Comment1",
                            'department': str(D3),
                            'department_pk': D3.pk,
                            'plant_died': None, 'seeded_date': None,
                            'inventory_date': None,
                            'location': None,
                        },
                    ],
                }
            ],
            indi.outplanting_audit,
        )

    def test_add_outpl(self):
        self.login("add-outpl")
        indi = Individual.objects.get(accession_number="1000")
        D1 = Department.objects.get(code="D1")
        D2 = Department.objects.get(code="D2")
        cf = self.get_changeform("individuals", "individual", pk=indi.pk)
        cf.assert_save_button(True)
        self.assertNotEqual([], cf.visible_fields())
        cf.save({
            "accession_number": "1234",  # won't be saved
            "outplanting_set-0-comment": "Comment1",
            # add outplanting
            "outplanting_set-TOTAL_FORMS": 2,
            "id_outplanting_set-1-id": "",
            "id_outplanting_set-1-individual": str(indi.pk),
            "outplanting_set-1-department": str(D2.pk),
            "outplanting_set-1-date": "2022-01-01",
            "outplanting_set-1-comment": "Comment2",
        }, expect_fields=False)

        indi.refresh_from_db()
        self.assertEqual("1000", indi.accession_number) # it's unchanged!
        self.assertEqual(
            ["D1", "D2"],
            list(indi.outplanting_set.all().order_by("pk").values_list("department__code", flat=True))
        )
        self.assertEqual(
            ["Comment1", "Comment2"],
            list(indi.outplanting_set.all().order_by("pk").values_list("comment", flat=True))
        )

        today = timezone.now().date().isoformat()
        self.assertEqualNice(
            [
                {
                    'date': today,
                    'user': "-",
                    'user_pk': None,
                    'outplantings': [
                        {
                            'pk': indi.outplanting_set.order_by("pk")[0].pk,
                            'department': str(D1),
                            'department_pk': D1.pk,
                            'location': None, 'seeded_date': None, 'date': None,
                            'inventory_date': None,
                            'plant_died': None,
                            'comment': None,
                        }
                    ],
                },
                {
                    'date': today,
                    'user': self.user_add_outpl.username,
                    'user_pk': self.user_add_outpl.pk,
                    'outplantings': [
                        {
                            'pk': indi.outplanting_set.order_by("pk")[0].pk,
                            'date': None,
                            'comment': "Comment1",
                            'department': str(D1),
                            'department_pk': D1.pk,
                            'plant_died': None, 'seeded_date': None,
                            'inventory_date': None,
                            'location': None,
                        },
                        {
                            'pk': indi.outplanting_set.order_by("pk")[1].pk,
                            'date': "2022-01-01",
                            'comment': "Comment2",
                            'department': str(D2),
                            'department_pk': D2.pk,
                            'plant_died': None, 'seeded_date': None,
                            'inventory_date': None,
                            'location': None,
                        },
                    ],
                }
            ],
            indi.outplanting_audit,
        )
