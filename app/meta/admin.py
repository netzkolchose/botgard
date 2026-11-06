from django.contrib import admin
from django.utils.translation import gettext_lazy as _

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


class ProjectAdmin(ConfigurableTable):
    form = ProjectForm

    list_display = (
        'change_link_decorator',
        'abbreviation',
        'title',
        'purpose',
        'manager',
        'partner',
    )

    blacklist = (
        'id', '__str__',
    )

    list_display_links = ()
    search_fields = search_fields_compatible((
        '@full_name_generated',
        'purpose',
        'manager',
        'partner',
        'funding',
    ))
    list_filter = (
        ("created_by__username", ForeignKeyFilter),
        ("modified_by__username", ForeignKeyFilter),
    )
    fieldsets = (
        (None, {
            "fields": (
                ("abbreviation", "title"),
                ("date_start", "date_end"),
                "purpose",
                "manager",
                "partner",
                "funding",
                "comment",
            ),
        }),
    )

    class Media:
        css = {"screen": ('BotGard/css_dropdown/css_dropdown.css',)}


admin.site.register(Literature, LiteratureAdmin)
admin.site.register(Project, ProjectAdmin)
