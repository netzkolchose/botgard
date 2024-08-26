import datetime
import csv
from pathlib import Path
from copy import deepcopy
from typing import Type, List

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import models

from botman.models import BotanicGarden
from species.models import Family, Species
from individuals.models import Individual


class Command(BaseCommand):
    help = 'Add demo data to the database'

    def handle(self, *args, **options):
        add_demo_data()



def add_demo_data():
    demo_path = Path(settings.BASE_DIR) / "demo-data"

    garden_list = _read_csv(demo_path / "garden.csv")
    family_list = _read_csv(demo_path / "family.csv")
    species_list = _read_csv(demo_path / "species.csv")
    individual_list = _read_csv(demo_path / "individual.csv")

    garden_id_map = _add_to_database(BotanicGarden, garden_list)
    family_id_map = _add_to_database(Family, family_list)

    for data in species_list:
        data["family"] = family_id_map[int(data["family"])]

    species_id_map = _add_to_database(Species, species_list)

    for data in individual_list:
        data["source"] = garden_id_map[int(data["source"])]
        data["ipen_garden_code"] = garden_id_map[int(data["ipen_garden_code"])]
        data["species"] = species_id_map[int(data["species"])]

    _add_to_database(Individual, individual_list)


def _read_csv(filename: Path):
    with filename.open() as fp:
        data_list = list(csv.DictReader(fp))

    for entry in data_list:
        entry["id"] = int(entry["id"])

    return data_list


def _add_to_database(Model: Type[models.Model], data_list: List[dict]) -> dict:
    id_map = {}
    for data in data_list:
        data = deepcopy(data)

        table_id = data.pop("id")

        for key, value in data.items():
            if key.endswith("_date"):
                if not value.strip():
                    data[key] = None

        instance = Model.objects.create(**data)

        id_map[table_id] = instance

    return id_map




