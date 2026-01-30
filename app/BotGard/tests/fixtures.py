import pathlib
import random
import sys
from copy import deepcopy
from typing import Dict, Set

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group

DATA_PATH = pathlib.Path(__file__).resolve().parent.joinpath("data")


USERS = [
    {"username": "User1", "password": "the-secret", "superuser": True},
    {"username": "User2", "password": "the-secret"},
]

BGCI_GARDENS = [
    {"bgci_id": 23, "ipen_code": "GARD", "name": "BGCI1", "type": "Botanic Garden/Arboretum", "bgci_data": {"some": "data"}},
]

BOTANIC_GARDENS = [
    {"name": "Garden 1", "code": "GARD1", "address": "Line 1\nLine 2\nLine 3\nLine 4"},
    {"name": "Garden 2", "code": "GARD2", "address": "Linä 1\nLine,2\nLine\\n'3\nLine\"4"},
    {"name": "Garden 3", "code": "GARD3"}
]

OUTGOING_ORDERS = [
    {"garden": "Garden 1", "user": "User1", "order_text": "Salat alles"},
    {"garden": "Garden 2", "user": "User2", "order_text": "123ABC"},
]

EXTERNAL_CATALOGS = [
    {"garden": "Garden 1"},
    {"garden": "Garden 2"},
]

FAMILIES = [
    {"family": "Family 1", "genus": "Genus 1"},
    {"family": "Family 2", "genus": "Genus 1"},
    {"family": "Family 2", "genus": "Genus 2"},
]

SPECIES = [
    {"species": "Species 1", "family": "Family 1/Genus 1"},
    {"species": "Species 2", "family": "Family 2/Genus 1"},
    {"species": "Species 3", "family": "Family 2/Genus 2"},
]

TERRITORIES = [
    {"code": "T1", "name": "Territory 1"},
    {"code": "T2", "name": "Territory 2"},
    {"code": "T3", "name": "Territory 3"},
]

DEPARTMENTS = [
    {"code": "D1", "name": "Department 1", "territory": "T1"},
    {"code": "D2", "name": "Department 2", "territory": "T2"},
    {"code": "D3", "name": "Department 3", "territory": "T3"},
    {"code": "D4", "name": "Department 4", "territory": "T3"},
]

ENTRIES = [
    {"accession_number": 10, "species": "Species Unknown"},
]

INDIVIDUALS = [
    {"accession_number": 1000, "species": "Species 1", "source": "Garden 1", "found_country": "AU"},
    {"accession_number": 1001, "species": "Species 2", "source": "Garden 2", "found_country": "IT"},
    {"accession_number": 1002, "species": "Species 3", "source": "Garden 1", "found_country": "CZ"},
]

OUTPLANTINGS = [
    {"department": "D1", "individual": 1000},
    {"department": "D1", "individual": 1001},
    {"department": "D2", "individual": 1002, "date": "2000-01-01"},
    {"department": None, "individual": 1002},
    {"department": None, "individual": 1001, "date": "2000-01-01"},
]

LABELS = [
    {"id_name": "A1", "format": "svg", "display_name": "Address Label 1", "type": "garden", "markup": "label-garden.svg"},
    {"id_name": "I1", "format": "svg", "display_name": "Individual Label 1", "type": "individual", "markup": "label-individual.svg"},
    {"id_name": "A2", "format": "csv", "display_name": "Address Label 2", "type": "garden", "markup": "label-garden.csv"},
    {"id_name": "I2", "format": "html", "display_name": "Individual Label 2", "type": "individual", "markup": "label-individual.html", "page_markup": "label-individual-page.html"},
]

HERBARIA = [
    {"name": "Herbarium1", "comment": "A loose collection"},
]

HERBARIUM_SPECIMENS = [
    {"herbarium": "Herbarium1", "individual": 1002, "collector": "User1"},
]

BASIC_TICKETS = [
    {"title": "Ticket 1", "due_date": "2030-01-01", "current_state": "N", "created_by": "User1", "directed_to": "User2"},
    {"title": "Ticket 2", "due_date": "2030-01-02", "current_state": "A", "created_by": "User2", "directed_to": "User1"},
    {"title": "Ticket 3", "due_date": "2030-01-03", "current_state": "F", "created_by": "User1", "directed_to": "User2"},
]

SEED_CATALOGS = [
    {"release_date": "2000-01-01", "valid_until_date": "2001-01-01", "title": "Index S"},
]

RANDOM_AUTHORS = ["A. Cunn.", "Baill.", "C. Morren"]


def log(*args, **kwargs):
    if 0:
        kwargs["file"] = sys.stderr
        print(*args, **kwargs)


def create_test_fixtures():
    from botman.models import BGCIGarden, BotanicGarden, ExternalCatalog, ExternalCatalogArchive, OutgoingOrder
    from entrybook.models import Entry
    from species.models import Family, Species
    from individuals.models import Department, Territory, Individual, Outplanting, Seed
    from herbaria.models import Herbarium, HerbariumSpecimen
    from labels.models import LabelDefinition
    from tickets.models import BasicTicket, LaserGravurTicket
    from seedcatalog.models import SeedCatalog

    UserModel = get_user_model()

    rnd = random.Random(42)

    log("creating UserModel")
    for i, data in enumerate(USERS):
        kwargs = dict(
            username=data["username"],
            email="%s@example.com" % data["username"],
            password=data["password"]
        )
        if data.get("superuser"):
            UserModel.objects.create_superuser(**kwargs)
        else:
            UserModel.objects.create_user(**kwargs)

        # print("U", UserModel.objects.get(username=data["username"]).is_superuser)

    log("creating BGCIGarden")
    for i, data in enumerate(BGCI_GARDENS):
        BGCIGarden.objects.create(**data)

    log("creating BotanicGarden")
    for i, data in enumerate(BOTANIC_GARDENS):
        BotanicGarden.objects.create(
            name=data["name"],
            code=data.get("code") or data["name"].replace(" ", "-")[-6:],
            number=data.get("number") or i,
            address=data.get("address"),
        )

    log("creating ExternalCatalog")
    for i, data in enumerate(EXTERNAL_CATALOGS):
        data = deepcopy(data)
        data["garden"] = BotanicGarden.objects.get(name=data["garden"])
        ExternalCatalog.objects.create(**data)
        ExternalCatalogArchive.objects.create(**data)

    log("creating OutgoingOrder")
    for i, data in enumerate(OUTGOING_ORDERS):
        data = deepcopy(data)
        data["garden"] = BotanicGarden.objects.get(name=data["garden"])
        data["user"] = UserModel.objects.get(username=data["user"])
        OutgoingOrder.objects.create(**data)

    log("creating Entry")
    for i, data in enumerate(ENTRIES):
        Entry.objects.create(
            **data,
            ipen_accession_number=data["accession_number"],
            seed_available=False, seed_in_stock=False,
        )

    log("creating Family")
    for i, data in enumerate(FAMILIES):
        Family.objects.create(
            family=data["family"],
            subfamily=data.get("subfamily") or "",
            tribus=data.get("tribus") or "",
            subtribus=data.get("subtribus") or "",
            genus=data["genus"],
            genus_author=data.get("genus_author") or rnd.choice(RANDOM_AUTHORS),
        )

    log("creating Species")
    for i, data in enumerate(SPECIES):
        family, genus = data["family"].split("/")
        Species.objects.create(
            family=Family.objects.get(family=family, genus=genus),
            species=data["species"],
            species_author=rnd.choice(RANDOM_AUTHORS),
            subspecies=data.get("subspecies") or "",
            subspecies_author=rnd.choice(RANDOM_AUTHORS),
            variety="",
            variety_author="",
            form="",
            form_author=rnd.choice(RANDOM_AUTHORS),
            cultivar="",
            deutscher_name="",
            synonyme="",
            area_of_distribution_etikettxt="",
            area_of_distribution_background="",
            protection_of_species="",
            poisonous_plant=False,
            lifeform="",
            nomenclature_checked=True,
        )

    log("creating Territory")
    for i, data in enumerate(TERRITORIES):
        Territory.objects.create(
            code=data["code"],
            name=data["name"],
        )

    log("creating Department")
    for i, data in enumerate(DEPARTMENTS):
        Department.objects.create(
            territory=Territory.objects.get(code=data["territory"]),
            code=data["code"],
            name=data["name"],
        )

    log("creating Individual and Seed")
    for i, data in enumerate(INDIVIDUALS):
        Individual.objects.create(
            accession_number=data["accession_number"],
            accession_extension="",
            species=Species.objects.get(species=data["species"]),    
            species_checked_by="",
            came_as_species="",
            ipen_country=data["found_country"],
            ipen_transfer_restricted="0",
            ipen_garden_code=BotanicGarden.objects.get(name=data["source"]),
            ipen_accession_number=data["accession_number"],
            source=BotanicGarden.objects.get(name=data["source"]),
            source_date=None,
            came_in_as="",
            found_country=data["found_country"],
            found_text="",
            collector_name="",
            collector_number="",
            collector_date=None,
            gender="",
            comment="",
    
            seed_available=True,
            order_number=i,
    
            seed_collector_date=None,
            seed_in_stock=True,
    
            sowing_number="",
        )

    log("creating Outplanting")
    for data in OUTPLANTINGS:
        Outplanting.objects.create(
            department=(
                Department.objects.get(code=data["department"])
                if data.get("department") else None
            ),
            individual=Individual.objects.get(accession_number=data["individual"]),
            seeded_date=None,
            date=data.get("date"),
            plant_died=None,
        )

    log("creating Herbarium & HerbariumSpecimen")
    for data in HERBARIA:
        Herbarium.objects.create(**data)

    for data in HERBARIUM_SPECIMENS:
        data = deepcopy(data)
        data["herbarium"] = Herbarium.objects.get(name=data["herbarium"])
        data["individual"] = Individual.objects.get(accession_number=data["individual"])
        data["collector"] = UserModel.objects.get(username=data["collector"])
        HerbariumSpecimen.objects.create(**data)

    log("creating LabelDefinition")
    for data in LABELS:
        LabelDefinition.objects.create(
            id_name=data["id_name"],
            display_name=data["display_name"],
            type=data["type"],
            markup=(DATA_PATH / data["markup"]).read_text(),
            page_markup=(DATA_PATH / data["page_markup"]).read_text() if data.get("page_markup") else None,
            format=data.get("format", "svg"),
        )

    log("creating Tickets")
    for data in BASIC_TICKETS:
        data = dict(
            title=data["title"],
            description=data.get("description") or "",
            due_date=data["due_date"],
            ticket_type="basic",
            current_state=data["current_state"],
            created_by=UserModel.objects.get(username=data["created_by"]),
            directed_to=UserModel.objects.get(username=data["directed_to"]),
        )
        BasicTicket.objects.create(**data)
        LaserGravurTicket.objects.create(**data)

    log("creating SeedCatalog")
    for data in SEED_CATALOGS:
        SeedCatalog.objects.create(**data)


def create_permission_group(name: str, permissions: Dict[str, Set[str]]) -> Group:
    group = Group.objects.create(name=name)

    perms = []
    for key, levels in permissions.items():
        app_name, model_name = key.split(".")
        for level in levels:
            perms.append(
                Permission.objects.get(
                    content_type__app_label=app_name,
                    content_type__model=model_name,
                    codename=f"{level}_{model_name}",
                )
            )

    group.permissions.set(perms)

    return group
