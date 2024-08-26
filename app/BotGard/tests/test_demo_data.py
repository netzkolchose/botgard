import re

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.admindocs.views import simplify_regex
from django.utils import timezone
from django.contrib.auth import get_user_model

from individuals.models import Seed
from seedcatalog.models import SeedCatalog

from botman.management.commands.botgard_demo_data import add_demo_data


class TestDemoData(TestCase):

    def test_add_demo_data(self):
        add_demo_data()
