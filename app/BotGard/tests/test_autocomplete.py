import json
from multiprocessing.connection import families

from django.contrib.admindocs.views import simplify_regex

from herbaria.models.specimen import HERBARIUM_SPECIMEN_TYPES
from .base import *


class TestAutocomplete(TestBase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserModel.objects.create_superuser(
            username="User1",
            password="the-secret",
        )
        cls.garden = BotanicGarden.objects.create(
            code="GARD1",
            name="Garden 1",
        )
        cls.territory = Territory.objects.create(
            code="T1",
            name="Territory 1",
        )
        cls.families = [
            Family.objects.create(
                family=f"Family{i}",
                genus=f"Genus{i}",
            )
            for i in range(11)
        ]
        Family.objects.create(
            family="Family-Unused",
            genus="Genus-Unused",
        )
        species_names = [
            "chinensis",
            "distichum",
            "esculentus",
            "manihot",
            "alba",
            "cephalonica",
        ]
        cls.species = [
            Species.objects.create(
                family=cls.families[i % len(families)],
                species=f"{species_names[i % len(species_names)]}{i}",
            )
            for i in range(50)
        ]
        cls.individuals = [
            Individual.objects.create(
                accession_number=f"{i:04}",
                species=cls.species[i % len(cls.species)],
                ipen_garden_code=cls.garden,
                ipen_accession_number=f"{i}:04",
                seed_available=True,
                seed_in_stock=False,
            )
            for i in range(len(cls.species))
        ]
        cls.herbarium = Herbarium.objects.create(
            name="Herb1",
        )
        cls.specimens = [
            HerbariumSpecimen.objects.create(
                herbarium=cls.herbarium,
                individual=cls.individuals[(i * 3) % len(cls.individuals)],
                collector=cls.user,
                specimen_type=HERBARIUM_SPECIMEN_TYPES[i % len(HERBARIUM_SPECIMEN_TYPES)][0],
            )
            for i in range(9)
        ]

    def setUp(self):
        self.login("User1")

    def request_autocomplete(self, params: dict) -> dict:
        response = self.client.get(reverse("ajax:model_json") + "?" + urllib.parse.urlencode(params))
        self.assertEqual(200, response.status_code)
        return json.loads(response.content.decode())

    def test_autocomplete_direct(self):
        """
        Autocomplete for model field
        """
        response = self.request_autocomplete({
            "id": "individuals-individual-id_name_generated",
            "term": "ch",
        })
        #print(json.dumps(response, indent=4))
        self.assertEqual(
            {
                "state": "many",
                "items": [
                    "0000 (Genus0 chinensis0)",
                    "0001 (Genus1 distichum1)",
                    "0006 (Genus0 chinensis6)",
                    "0007 (Genus1 distichum7)",
                    "0012 (Genus0 chinensis12)",
                    "0013 (Genus1 distichum13)",
                    "0018 (Genus0 chinensis18)",
                    "0019 (Genus1 distichum19)",
                    "0024 (Genus0 chinensis24)",
                    "0025 (Genus1 distichum25)"
                ]
            },
            response,
        )

        self.assertEqual(
            {"state": "none", "items": []},
            self.request_autocomplete({
                "id": "individuals-individual-id_name_generated",
                "term": "blub",
            })
        )

    def test_autocomplete_limit(self):
        """
        autocomplete for individuals iff they are referenced by HerbariumSpecimen.individual
        :return:
        """
        response = self.request_autocomplete({
            "id": "individuals-individual-id_name_generated",
            "term": "ch",
            "limit": "herbaria-herbariumspecimen-individual",
        })
        #print(json.dumps(response, indent=4))
        self.assertEqual(
            {
                "state": "many",
                "items": [
                    "0000 (Genus0 chinensis0)",
                    "0006 (Genus0 chinensis6)",
                    "0012 (Genus0 chinensis12)",
                    "0018 (Genus0 chinensis18)",
                    "0024 (Genus0 chinensis24)",
                ]
            },
            response,
        )

    def test_autocomplete_limit_2(self):
        """
        autocomplete for Family.genus iff in Individual.species.family
        """
        self.login("User1")

        response = self.request_autocomplete({
            "id": "species-family-genus",
            "term": "Genus",
        })
        #print(json.dumps(response, indent=4))
        self.assertEqual(
            {
                "state": "many",
                "items": [
                    "Genus-Unused",
                    "Genus0",
                    "Genus1",
                    "Genus10",
                    "Genus2",
                    "Genus3",
                    "Genus4",
                    "Genus5",
                    "Genus6",
                    "Genus7",
                ]
            },
            response,
        )

        response = self.request_autocomplete({
            "id": "species-family-genus",
            "term": "Genus",
            "limit": "individuals-individual-species__family",
        })
        #print(json.dumps(response, indent=4))
        self.assertEqual(
            {
                "state": "many",
                "items": [
                    "Genus0",
                    "Genus1",
                ]
            },
            response,
        )

    def assert_changelist_autocomplete_limits(
            self,
            app_name: str,
            model_name: str,
            expected_autocompletes: dict,
    ):
        """
        Load changelist with all possible columns.
        Assert that the filter widgets have the expected autocomplete settings.
        Also assert that there is no filter widget with a data-ac-limit that is not expected
        """
        cl = self.get_changelist(app_name, model_name)
        cl.set_columns(cl.get_all_possible_columns())
        msg = json.dumps(cl.get_header_autocomplete_settings(), indent=4)
        autocompletes = cl.get_header_autocomplete_settings()
        for key, value in expected_autocompletes.items():
            self.assertEqual(value, autocompletes.get(key), f"For field '{key}', got:\n{msg}")
        for key, value in autocompletes.items():
            if value.get("limit"):
                if key not in expected_autocompletes:
                    raise AssertionError(f"Got unexpected autocomplete-limit for field '{key}': {value}, got:\n{msg}")
            else:
                # if it's not a decorator function, expect full app_name-model_name-field id
                if not key.endswith("_decorator"):
                    self.assertEqual(
                        f"{app_name}-{model_name}-{key}",
                        value["id"],
                        f"Unexpected id for field '{key}', got:\n{msg}"
                    )
                # otherwise, expect to at least start with app_name-model_name
                else:
                    if not value["id"].startswith(f"{app_name}-{model_name}-"):
                        raise AssertionError(
                            f"Unexpected start of id for field '{key}': {value['id']}, got:\n{msg}"
                        )
                    self.assertNotIn("decorator", value["id"], f"For field '{key}', got:\n{msg}")

    def test_autocomplete_limit_in_changelist_species(self):
        self.assert_changelist_autocomplete_limits(
            "species", "species",
            {
                "created_by": {
                    "id": "auth-user-username",
                    "limit": "species-species-created_by"
                },
                "modified_by": {
                    "id": "auth-user-username",
                    "limit": "species-species-modified_by"
                },
                "family": {
                    "id": "species-family-full_name_generated",
                    "limit": "species-species-family"
                },
                "family_single": {
                    "id": "species-family-family",
                    "limit": "species-species-family"
                },
                "genus_single": {
                    "id": "species-family-genus",
                    "limit": "species-species-family"
                },
                "literature": {
                    "id": "literature-literature-full_name_generated",
                    "limit": "species-species-literature"
                },
                "literature_distribution": {
                    "id": "literature-literature-full_name_generated",
                    "limit": "species-species-literature_distribution"
                },
                "literature_german_name": {
                    "id": "literature-literature-full_name_generated",
                    "limit": "species-species-literature_german_name"
                },
            }
        )

    def test_autocomplete_limit_in_changelist_individual(self):
        self.assert_changelist_autocomplete_limits(
            "individuals", "individual",
            {
                "created_by": {
                    "id": "auth-user-username",
                    "limit": "individuals-individual-created_by"
                },
                "modified_by": {
                    "id": "auth-user-username",
                    "limit": "individuals-individual-modified_by"
                },
                "user": {
                    "id": "auth-user-username",
                    "limit": "individuals-individual-user"
                },
                "source": {
                    "id": "botman-botanicgarden-full_name_generated",
                    "limit": "individuals-individual-source"
                },
                "family_single": {
                    "id": "individuals-individual-species__family__family",
                    "limit": "individuals-individual-species__family"
                },
                "species_link_decorator": {
                    "id": "species-species-full_name_generated",
                    "limit": "individuals-individual-species"
                },
                "etikett_detail_decorator": {
                    "id": "species-species-area_of_distribution_background",
                    "limit": "individuals-individual-species"
                },
                "genus_single": {
                    "id": "individuals-individual-species__family__genus",
                    "limit": "individuals-individual-species__family"
                },
                "etikett_text_decorator": {
                    "id": "species-species-area_of_distribution_etikettxt",
                    "limit": "individuals-individual-species"
                },
                "literature": {
                    "id": "literature-literature-full_name_generated",
                    "limit": "individuals-individual-literature"
                },
                "projects_decorator": {
                    "id": "meta-project-full_name_generated",
                    "limit": "individuals-individual-projects"
                },
            }
        )

    def test_autocomplete_limit_in_changelist_herbariumspecimen(self):
        self.assert_changelist_autocomplete_limits(
            "herbaria", "herbariumspecimen",
            {
                "created_by": {
                    "id": "auth-user-username",
                    "limit": "herbaria-herbariumspecimen-created_by"
                },
                "modified_by": {
                    "id": "auth-user-username",
                    "limit": "herbaria-herbariumspecimen-modified_by"
                },
                "herbarium": {
                    "id": "herbaria-herbarium-name",
                    "limit": "herbaria-herbariumspecimen-herbarium"
                },
                "collector": {
                    "id": "auth-user-username",
                    "limit": "herbaria-herbariumspecimen-collector"
                },
                "individual_link_decorator": {
                    "id": "individuals-individual-id_name_generated",
                    "limit": "herbaria-herbariumspecimen-individual"
                }
            }
        )

    def test_autocomplete_limit_in_changelist_department(self):
        self.assert_changelist_autocomplete_limits(
            "individuals", "department",
            {
                "created_by": {
                    "id": "auth-user-username",
                    "limit": "individuals-department-created_by"
                },
                "modified_by": {
                    "id": "auth-user-username",
                    "limit": "individuals-department-modified_by"
                },
                "territory": {
                    "id": "individuals-territory-name_generated",
                    "limit": "individuals-department-territory"
                },
            }
        )

    def test_autocomplete_limit_in_changelist_outgoingorder(self):
        self.assert_changelist_autocomplete_limits(
            "botman", "outgoingorder",
            {
                "user": {
                    "id": "auth-user-username",
                    "limit": "botman-outgoingorder-user"
                },
                "garden_link_decorator": {
                    "id": "botman-botanicgarden-full_name_generated",
                    "limit": "botman-outgoingorder-garden"
                },
                "garden_email_decorator": {
                    "id": "botman-botanicgarden-email",
                    "limit": "botman-outgoingorder-garden"
                },
                "user_email_decorator": {
                    "id": "auth-user-email",
                    "limit": "botman-outgoingorder-user"
                },
                "catalog_date": {
                    "id": "botman-botanicgarden-catalog_date_generated",
                    "limit": "botman-outgoingorder-garden"
                }
            }
        )

    def test_autocomplete_limit_in_changelist_externalcatalog(self):
        self.assert_changelist_autocomplete_limits(
            "botman", "externalcatalog",
            {
                "num_orders_decorator": {
                    "id": "botman-botanicgarden-num_orders_generated",
                    "limit": "botman-externalcatalog-garden"
                },
                "garden_link_decorator": {
                    "id": "botman-botanicgarden-full_name_generated",
                    "limit": "botman-externalcatalog-garden"
                }
            }
        )

    def test_autocomplete_limit_in_changelist_botanicgarden(self):
        self.assert_changelist_autocomplete_limits(
            "botman", "botanicgarden",
            {
                "created_by": {
                    "id": "auth-user-username",
                    "limit": "botman-botanicgarden-created_by"
                },
                "modified_by": {
                    "id": "auth-user-username",
                    "limit": "botman-botanicgarden-modified_by"
                },

            }
        )

    def test_autocomplete_limit_in_changelist_entry(self):
        self.assert_changelist_autocomplete_limits(
            "entrybook", "entry",
            {
                "created_by": {
                    "id": "auth-user-username",
                    "limit": "entrybook-entry-created_by"
                },
                "modified_by": {
                    "id": "auth-user-username",
                    "limit": "entrybook-entry-modified_by"
                },
                "user": {
                    "id": "auth-user-username",
                    "limit": "entrybook-entry-user"
                },
                "department_decorator": {
                    "id": "individuals-department-code",
                    "limit": "entrybook-entry-department"
                },
                "literature": {
                    "id": "literature-literature-full_name_generated",
                    "limit": "entrybook-entry-literature"
                },
            }
        )
