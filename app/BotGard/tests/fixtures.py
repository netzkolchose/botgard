import pathlib
import random
import sys

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

DATA_PATH = pathlib.Path(__file__).resolve().parent.joinpath("data")


USERS = [
    {"username": "User1", "password": "the-secret", "superuser": True},
    {"username": "User2", "password": "the-secret"},
]


BOTANIC_GARDENS = [
    {"name": "Garden 1", "address": "Line 1\nLine 2\nLine 3\nLine 4"},
    {"name": "Garden 2", "address": "Linä 1\nLine,2\nLine\\n'3\nLine\"4"},
    {"name": "Garden 3"}
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

INDIVIDUALS = [
    {"accession_number": 1000, "species": "Species 1", "source": "Garden 1", "found_country": "AU"},
    {"accession_number": 1001, "species": "Species 2", "source": "Garden 2", "found_country": "IT"},
    {"accession_number": 1002, "species": "Species 3", "source": "Garden 1", "found_country": "CZ"},
]

OUTPLANTINGS = [
    {"department": "D1", "individual": 1000},
    {"department": "D1", "individual": 1001},
    {"department": "D2", "individual": 1002},
]

LABELS = [
    {"id_name": "A1", "display_name": "Address Label 1", "type": "garden", "svg_markup": "label-garden.svg"},
    {"id_name": "I1", "display_name": "Individual Label 1", "type": "individual", "svg_markup": "label-individual.svg"},
    {"id_name": "A2", "format": "csv", "display_name": "Address Label 2", "type": "garden", "svg_markup": "label-garden.csv"},
    #{"id_name": "I2", "format": "csv", "display_name": "Individual Label 2", "type": "individual", "svg_markup": "label-individual.csv"},
]

BASIC_TICKETS = [
    {"title": "Ticket 1", "due_date": "2030-01-01", "current_state": "N", "created_by": "User1", "directed_to": "User2"},
    {"title": "Ticket 2", "due_date": "2030-01-02", "current_state": "A", "created_by": "User2", "directed_to": "User1"},
    {"title": "Ticket 3", "due_date": "2030-01-03", "current_state": "F", "created_by": "User1", "directed_to": "User2"},
]

RANDOM_AUTHORS = ["A. Cunn.", "Baill.", "C. Morren"]


def log(*args, **kwargs):
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def create_test_fixtures():
    from botman.models import BotanicGarden
    from species.models import Family, Species
    from individuals.models import Department, Territory, Individual, Outplanting, Seed
    from labels.models import LabelDefinition
    from tickets.models import BasicTicket, LaserGravurTicket
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
            user = UserModel.objects.create_superuser(**kwargs)
            for p in Permission.objects.all():
                user.user_permissions.add(p)
        else:
            UserModel.objects.create_user(**kwargs)

        # print("U", UserModel.objects.get(username=data["username"]).is_superuser)

    log("creating BotanicGarden")
    for i, data in enumerate(BOTANIC_GARDENS):
        BotanicGarden.objects.create(
            name=data["name"],
            code=data.get("code") or data["name"].replace(" ", "-")[-6:],
            number=data.get("number") or i,
            address=data.get("address"),
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
            department=Department.objects.get(code=data["department"]),
            individual=Individual.objects.get(accession_number=data["individual"]),
            seeded_date=None,
            date=None,
            plant_died=None,
        )

    log("creating LabelDefinition")
    for data in LABELS:
        LabelDefinition.objects.create(
            id_name=data["id_name"],
            display_name=data["display_name"],
            type=data["type"],
            svg_markup=DATA_PATH.joinpath(data["svg_markup"]).open().read(),
            format=data.get("format", "svg"),
        )

    log("creating BasicTicket")
    for data in BASIC_TICKETS:
        BasicTicket.objects.create(
            title=data["title"],
            description=data.get("description") or "",
            due_date=data["due_date"],
            ticket_type="basic",
            current_state=data["current_state"],
            created_by=UserModel.objects.get(username=data["created_by"]),
            directed_to=UserModel.objects.get(username=data["directed_to"]),
        )
