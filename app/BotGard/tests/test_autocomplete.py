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

    def request_autocomplete(self, params: dict) -> dict:
        response = self.client.get(reverse("ajax:model_json") + "?" + urllib.parse.urlencode(params))
        self.assertEqual(200, response.status_code)
        return json.loads(response.content.decode())

    def test_autocomplete_individual(self):
        self.login("User1")

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

    def test_autocomplete_specimen(self):
        """
        autocomplete for individuals iff they are referenced by HerbariumSpecimen.individual
        :return:
        """
        self.login("User1")

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
