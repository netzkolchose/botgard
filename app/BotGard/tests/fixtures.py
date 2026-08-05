import pathlib
import random
import sys
from copy import deepcopy
from typing import Dict, Set

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group

from config_app.models import CUSTOM_PROPERTY_MODEL_CHOICES

DATA_PATH = pathlib.Path(__file__).resolve().parent.joinpath("data")


USERS = [
    {"username": "User1", "password": "the-secret", "superuser": True},
    {"username": "User2", "password": "the-secret"},
    {"username": "User3", "password": "the-secret", "superuser": True},
]

CUSTOM_PROPERTIES = [
    {"model": "botman.BotanicGarden", "type": "bool", "name": "garden_important"},
    {"model": "botman.BGCIGarden", "type": "text_long", "name": "bgci_comment"},
    {"model": "species.Species", "type": "bool", "name": "poisonous"},
    {"model": "species.Family", "type": "text", "name": "distinct", "choices": "No\nYes\nAlmost\n"},
    {"model": "entrybook.Entry", "type": "text", "name": "entry_comment"},
    {"model": "individuals.Territory", "type": "text", "name": "territory_comment"},
    {"model": "individuals.Department", "type": "text", "name": "department_comment"},
    {"model": "individuals.Individual", "type": "text", "name": "individual_comment"},
    {"model": "herbaria.Herbarium", "type": "text", "name": "herbarium_comment"},
    {"model": "herbaria.HerbariumSpecimen", "type": "text", "name": "specimen_comment"},
]

if missing_set := set(
        c[0]
        for c in CUSTOM_PROPERTY_MODEL_CHOICES
        if not list(filter(lambda p: p["model"] == c[0], CUSTOM_PROPERTIES))
):
    raise AssertionError(
        f"Not all custom property models in test fixtures\n{sorted(missing_set)}"
    )


BGCI_GARDENS = [
    {"bgci_id": 23, "ipen_code": "GARD", "name": "BGCI1", "type": "Botanic Garden/Arboretum", "bgci_data": {"some": "data"}},
]

BOTANIC_GARDENS = [
    {"name": "Garden 1", "code": "GARD1", "address": "Line 1\nLine 2\nLine 3\nLine 4"},
    {"name": "Garden 2", "code": "GARD2", "address": "Linä 1\nLine,2\nLine\\n'3\nLine\"4"},
    {"name": "Garden 3", "code": "GARD3", "custom_property": {"name": "garden_important", "value": True}},
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
    {"family": "Family 2", "genus": "Genus 1", "custom_property": {"name": "distinct", "value": "Yes"}},
    {"family": "Family 2", "genus": "Genus 2", "custom_property": {"name": "distinct", "value": "No"}},
]

SPECIES = [
    {"species": "Species 1", "family": "Family 1/Genus 1", "custom_property": {"name": "distinct", "value": "Almost"}},
    {"species": "Species 2", "family": "Family 2/Genus 1"},
    {"species": "Species 3", "family": "Family 2/Genus 2"},
]

TERRITORIES = [
    {"code": "T1", "name": "Territory 1", "custom_property": {"name": "territory_comment", "value": "Nice here"}},
    {"code": "T2", "name": "Territory 2"},
    {"code": "T3", "name": "Territory 3"},
]

DEPARTMENTS = [
    {"code": "D1", "name": "Department 1", "territory": "T1"},
    {"code": "D2", "name": "Department 2", "territory": "T2", "custom_property": {"name": "department_comment", "value": "Fresh air"}},
    {"code": "D3", "name": "Department 3", "territory": "T3"},
    {"code": "D4", "name": "Department 4", "territory": "T3"},
]

ENTRIES = [
    {"accession_number": 10, "species": "Species Unknown", "custom_property": {"name": "entry_comment", "value": "Bob Dobbs"}},
]

INDIVIDUALS = [
    {"accession_number": 1000, "species": "Species 1", "source": "Garden 1", "found_country": "AU", "custom_property": {"name": "individual_comment", "value": "A tree"}},
    {"accession_number": 1001, "species": "Species 2", "source": "Garden 2", "found_country": "IT", "accession_extension": "10"},
    {"accession_number": 1002, "species": "Species 3", "source": "Garden 1", "found_country": "CZ", "accession_extension": "20"},
    {"accession_number": 1003, "species": "Species 3", "source": "Garden 2", "found_country": "ES", "accession_extension": "W"},
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
    {"id_name": "A2", "format": "csv", "display_name": "Address Label 2", "type": "garden", "markup": "label-garden.csv"},
    {"id_name": "I1", "format": "svg", "display_name": "Individual Label 1", "type": "individual", "markup": "label-individual.svg"},
    {"id_name": "I2", "format": "html", "display_name": "Individual Label 2", "type": "individual", "markup": "label-individual.html", "page_markup": "label-individual-page.html"},
    {"id_name": "I3", "format": "csv", "display_name": "Individual Label 3", "type": "individual", "markup": "label-individual.csv"},
    {"id_name": "S1", "format": "svg", "display_name": "Specimen Label 1", "type": "herbarium_specimen", "markup": "label-specimen.svg"},
    {"id_name": "S2", "format": "csv", "display_name": "Specimen Label 2", "type": "herbarium_specimen", "markup": "label-specimen.csv"},
]

HERBARIA = [
    {"name": "Herbarium1", "comment": "A loose collection", "custom_property": {"name": "herbarium_comment", "value": "The world"}},
]

HERBARIUM_SPECIMENS = [
    {"herbarium": "Herbarium1", "individual": 1002, "collector": "User1", "custom_property": {"name": "specimen_comment", "value": "The leaf"}},
    {"herbarium": "Herbarium1", "individual": 1003, "collector": "User2"},
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
    from config_app.models import CustomProperty, PropertyValueText, PropertyValueBool

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

    log("creating CustomProperty")
    for prop in CUSTOM_PROPERTIES:
        CustomProperty.objects.create(**prop)

    def _add_prop(model, data: dict):
        if prop := data.get("custom_property"):
            is_bool = isinstance(prop["value"], bool)

            p = (PropertyValueBool if is_bool else PropertyValueText).objects.create(
                property=CustomProperty.objects.get(name=prop["name"]),
                value=prop["value"],
            )
            getattr(model, "custom_values_bool" if is_bool else "custom_values_text").add(p)

    log("creating BGCIGarden")
    for i, data in enumerate(BGCI_GARDENS):
        data = deepcopy(data)
        custom_prop = data.pop("custom_property", None)
        model = BGCIGarden.objects.create(**data)
        if custom_prop:
            _add_prop(model, {"custom_property": custom_prop})

    log("creating BotanicGarden")
    for i, data in enumerate(BOTANIC_GARDENS):
        model = BotanicGarden.objects.create(
            name=data["name"],
            code=data.get("code") or data["name"].replace(" ", "-")[-6:],
            number=data.get("number") or i,
            address=data.get("address"),
        )
        _add_prop(model, data)

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
        data = deepcopy(data)
        custom_prop = data.pop("custom_property", None)
        model = Entry.objects.create(
            **data,
            ipen_accession_number=data["accession_number"],
            seed_available=False, seed_in_stock=False,
        )
        if custom_prop:
            _add_prop(model, {"custom_property": custom_prop})

    log("creating Family")
    for i, data in enumerate(FAMILIES):
        model = Family.objects.create(
            family=data["family"],
            subfamily=data.get("subfamily") or "",
            tribus=data.get("tribus") or "",
            subtribus=data.get("subtribus") or "",
            genus=data["genus"],
            genus_author=data.get("genus_author") or rnd.choice(RANDOM_AUTHORS),
        )
        _add_prop(model, data)

    log("creating Species")
    for i, data in enumerate(SPECIES):
        family, genus = data["family"].split("/")
        model = Species.objects.create(
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
            nomenclature_checked=bool(data.get("nomenclature_checked")),
        )
        _add_prop(model, data)

    log("creating Territory")
    for i, data in enumerate(TERRITORIES):
        model = Territory.objects.create(
            code=data["code"],
            name=data["name"],
        )
        _add_prop(model, data)

    log("creating Department")
    for i, data in enumerate(DEPARTMENTS):
        model = Department.objects.create(
            territory=Territory.objects.get(code=data["territory"]),
            code=data["code"],
            name=data["name"],
        )
        _add_prop(model, data)

    log("creating Individual and Seed")
    for i, data in enumerate(INDIVIDUALS):
        model = Individual.objects.create(
            accession_number=data["accession_number"],
            accession_extension=data.get("accession_extension") or "",
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
        _add_prop(model, data)

    log("creating Outplanting")
    for data in OUTPLANTINGS:
        model = Outplanting.objects.create(
            department=(
                Department.objects.get(code=data["department"])
                if data.get("department") else None
            ),
            individual=Individual.objects.get(accession_number=data["individual"]),
            seeded_date=None,
            date=data.get("date"),
            plant_died=None,
        )
        _add_prop(model, data)

    log("creating Herbarium & HerbariumSpecimen")
    for data in HERBARIA:
        custom_prop = data.pop("custom_property", None)
        model = Herbarium.objects.create(**data)
        if custom_prop:
            _add_prop(model, {"custom_property": custom_prop})

    for data in HERBARIUM_SPECIMENS:
        data = deepcopy(data)
        custom_prop = data.pop("custom_property", None)
        data["herbarium"] = Herbarium.objects.get(name=data["herbarium"])
        data["individual"] = Individual.objects.get(accession_number=data["individual"])
        data["collector"] = UserModel.objects.get(username=data["collector"])
        model = HerbariumSpecimen.objects.create(**data)
        if custom_prop:
            _add_prop(model, {"custom_property": custom_prop})

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
        if model_name:
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
