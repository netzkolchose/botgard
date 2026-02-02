import os
import json
import time
from copy import deepcopy
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm
import requests

from botman.models import BGCIGarden


class Command(BaseCommand):
    help = """
    Import all gardens from https://gardensearch.bgci.org/
    This takes about 40 minutes because the scraper is polite
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "-c", "--cached", type=bool, nargs="?", default=False, const=True,
            help="Cache the downloaded data in `<projectdir>/.cache/bgci`",
        )

    def handle(self, *args, cached: bool = True, **options):
        import_bgci(cached=cached)


def import_bgci(cached: bool = False):
    CACHE_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".cache" / "bgci"
    # well, don't be over-polite.. The search interface https://gardensearch.bgci.org/search actually
    #   passes input changes to the backend un-debounced
    POLITE_SECONDS = .3
    if cached:
        os.makedirs(CACHE_PATH, exist_ok=True)

    page_num = 1
    num_pages = None
    data_list = []
    with tqdm(desc="get search pages") as progress:
        while True:
            cache_filename = CACHE_PATH / f"search-page-{page_num}.json"
            if cached and cache_filename.exists():
                data = json.loads(cache_filename.read_text())
            else:
                url = f"https://datatools.bgci.org/api/gardens?filter[type]=1,2,3,4,5,6,7,8,9,10,11,12,13,14&sort=relevance&page[number]={page_num}&page[size]=100"
                data = requests.get(url).json()
                if cached:
                    cache_filename.write_text(json.dumps(data))
                time.sleep(POLITE_SECONDS)

            data_list.extend(data["data"])

            if num_pages is None:
                num_pages = data["meta"]["last_page"]
                progress.total = num_pages - 1
            else:
                if page_num >= num_pages:
                    break
                else:
                    page_num += 1
                    progress.update()

    for entry in tqdm(data_list, desc="download gardens"):
        bgci_id = entry["id"]

        if BGCIGarden.objects.filter(bgci_id=bgci_id).exists():
            continue

        cache_filename = CACHE_PATH / f"id-{bgci_id}.json"
        if cached and cache_filename.exists():
            data = json.loads(cache_filename.read_text())
        else:
            url = f"https://datatools.bgci.org/api/gardens/{bgci_id}?all_attributes=true&last_updates=true"
            data = requests.get(url).json()
            if cached:
                cache_filename.write_text(json.dumps(data))
            time.sleep(POLITE_SECONDS)

        try:
            data = data["data"]
            location = data["location_primary"] or {}
            garden_type = data["attributes"]["organisation_type"]["value"]
            if isinstance(garden_type, list):
                garden_type = "/".join(garden_type)
            if garden_type and len(garden_type) > 128:
                garden_type = f"{garden_type[:126]}.."

            # remove all the attributes, it's a lot of data without much use for BotGard
            slim_data = deepcopy(data)
            slim_data.pop("attributes", None)

            BGCIGarden.objects.create(
                bgci_id=bgci_id,
                ipen_code=data["index_herbariorum_code"],
                name=data["organisation_name"],
                type=garden_type,
                website=data["website"],
                phone=data["phone"],
                email=data["email_public"],
                country=(location.get("country_code") or "xx").lower(),
                city=location.get("city"),
                postal_code=location.get("postal_code"),
                address="\n".join(filter(bool, [
                    location.get("address_1"),
                    location.get("address_2"),
                ])) or None,
                bgci_data=slim_data,
            )
        except:
            print(json.dumps(data, indent=2))
            raise

