import re
import pprint
import secrets
import webbrowser
import itertools
from pathlib import Path
import tempfile
from typing import Dict, Set, Optional, Type, Callable

from django.test import TestCase, Client
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.db import models
from django.utils import timezone
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, Group
from django.contrib.auth import get_user_model

import bs4

from botman.models import *
from entrybook.models import *
from species.models import *
from individuals.models import *
from labels.models import *
from tickets.models import *
from seedcatalog.models import *

from .fixtures import create_permission_group, create_test_fixtures
from config_app.management.commands.botgard_update_config import update_config_in_database


class TestBase(TestCase):

    def get_form_data(self, form: bs4.PageElement) -> dict:
        data = {}

        for inp in form.find_all("input"):
            if "value" in inp.attrs and inp.attrs["type"] != "submit":
                data[inp.attrs["name"]] = inp.attrs["value"]

        for inp in form.find_all("textarea"):
            if inp.text:
                data[inp.attrs["name"]] = inp.text

        for inp in form.find_all("select"):
            val = None
            for opt in inp.find_all("option"):
                if value := opt.attrs.get("value"):
                    if "selected" in opt.attrs:
                        val = value
                        break
            if val is not None:
                data[inp.attrs["name"]] = val

        return data
