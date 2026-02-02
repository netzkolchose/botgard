import datetime
import csv
from pathlib import Path
from copy import deepcopy
from typing import Type, List, Union

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import models

from botman.models import BotanicGarden
from labels.models import LabelDefinition
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

    garden_id_map = _add_to_database(BotanicGarden, "name", garden_list)
    family_id_map = _add_to_database(Family, ["family", "genus"], family_list)

    for data in species_list:
        data["family"] = family_id_map[int(data["family"])]

    species_id_map = _add_to_database(Species, ["species", "family"], species_list)

    for data in individual_list:
        data["source"] = garden_id_map[int(data["source"])]
        data["ipen_garden_code"] = garden_id_map[int(data["ipen_garden_code"])]
        data["species"] = species_id_map[int(data["species"])]

    _add_to_database(Individual, "accession_number", individual_list)

    label_list = [
        dict(
            id=1,
            id_name="individual-laser-60x40",
            display_name="Individuum lasercut 60x40mm",
            type="individual",
            format="svg",
            markup=(demo_path / "labels" / "individual-lasercut-60x40.svg").read_text(),
        ),
        dict(
            id=2,
            id_name="individual-multipage-html",
            display_name="Individuum mehrseitig",
            type="individual",
            format="html",
            markup=(demo_path / "labels" / "individual-multipage-inner.html").read_text(),
            page_markup=(demo_path / "labels" / "individual-multipage-outer.html").read_text(),
        ),
        dict(
            id=3,
            id_name="individual-table",
            display_name="Individuum Tabelle",
            type="individual",
            format="csv",
            markup=(demo_path / "labels" / "individual-table.txt").read_text(),
        ),
        dict(
            id=4,
            id_name="herbarium-specimen-60x40",
            display_name="Herbarbeleg",
            type="herbarium_specimen",
            format="svg",
            markup=(demo_path / "labels" / "herbarium-specimen-60x40.svg").read_text(),
        ),
        dict(
            id=4,
            id_name="shipping-89x36",
            display_name="Versandadresse",
            type="garden",
            format="svg",
            markup=(demo_path / "labels" / "shipping-89x36.svg").read_text(),
        ),
    ]

    _add_to_database(LabelDefinition, "id_name", label_list)


def _read_csv(filename: Path):
    with filename.open() as fp:
        data_list = list(csv.DictReader(fp))

    for entry in data_list:
        entry["id"] = int(entry["id"])

    return data_list


def _add_to_database(
        Model: Type[models.Model],
        unique_field: Union[str, List[str]],
        data_list: List[dict],
) -> dict:
    id_map = {}
    for data in data_list:
        data = deepcopy(data)

        table_id = data.pop("id")

        for key, value in data.items():
            if key.endswith("_date"):
                if not value.strip():
                    data[key] = None

        kwargs = {
            f: data[f]
            for f in ([unique_field] if isinstance(unique_field, str) else unique_field)
        }
        instance = Model.objects.filter(**kwargs).first()
        if instance is None:
            instance = Model.objects.create(**data)

        id_map[table_id] = instance

    return id_map




