import re
from typing import List

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django import forms
from django.db import transaction
from django.urls import re_path
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.template.response import TemplateResponse

from tools.search_fields import search_fields_compatible
from config_tables.admin import ConfigurableTable, ForeignKeyFilter

from .models import *


class LiteratureAdmin(ConfigurableTable):
    form = LiteratureForm

    list_display = (
        'change_link_decorator',
        'full_name_generated',
        'year',
        'keywords',
        'location',
    )

    blacklist = (
        'id', '__str__',
    )

    list_display_links = ()
    search_fields = search_fields_compatible((
        '@full_name_generated',
        'publisher',
        'keywords',
        'location',
    ))
    list_filter = (
        ("created_by__username", ForeignKeyFilter),
        ("modified_by__username", ForeignKeyFilter),
    )

    class Media:
        css = {"screen": ('BotGard/css_dropdown/css_dropdown.css',)}


admin.site.register(Literature, LiteratureAdmin)
