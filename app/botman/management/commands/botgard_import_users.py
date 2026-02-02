import datetime
import csv
import json
from pathlib import Path
from copy import deepcopy
from typing import Type, List

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model

from botman.models import BotanicGarden
from species.models import Family, Species
from individuals.models import Individual


class Command(BaseCommand):
    help = 'Import users from a dump file'

    def add_arguments(self, parser):
        parser.add_argument(
            "filename", type=str,
            help="Filename of a json formatted dumpdata file",
        )

    def handle(self, filename: str, **options):
        with open(filename) as fp:
            items = json.load(fp)

        import_users(items)


def import_users(items: List[dict]):
    FIELDS = [
        "password", "is_superuser", "username", "first_name", "last_name", "email",
        "is_staff", "is_active",
    ]
    User = get_user_model()

    num_imported = 0
    num_skipped = 0
    try:
        for item in items:
            if item["model"] == "auth.user":
                username = item["fields"]["username"]

                if User.objects.filter(username=username).exists():
                    num_skipped += 1
                else:
                    if _ask(username):
                        User.objects.create(**{
                            key: value
                            for key, value in item["fields"].items()
                            if key in FIELDS
                        })
                        num_imported += 1
    except KeyboardInterrupt:
        print()

    print(f"\n{num_imported} users imported, {num_skipped} existing users skipped")


def _ask(username: str) -> bool:
    while True:
        yesno = input(f"{username} [Y/n]: ").lower().strip()
        if yesno in ("y", ""):
            return True
        if yesno == "n":
            return False







