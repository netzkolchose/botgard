from django.contrib import admin
from django.contrib.admin.decorators import register
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django import forms
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import *

from tools.search_fields import search_fields_compatible
from config_tables.admin import ConfigurableTable, ForeignKeyFilter
from ajax.autocomplete import AutoCompleteForm
from labels.mass_action import add_label_mass_actions


@register(Herbarium)
class HerbariumAdmin(ConfigurableTable):
    form = AutoCompleteForm(Herbarium)
    list_display = (
        'change_link_decorator', 'date_created', 'name', 'comment',
    )
    blacklist = ('id', )
    list_filter = (
        ("created_by__username", ForeignKeyFilter),
        ("modified_by__username", ForeignKeyFilter),
    )


@register(HerbariumSpecimen)
class HerbariumSpecimenAdmin(ConfigurableTable):
    form = create_herbarium_specimen_form_class()
    list_display = (
        'change_link_decorator',
        'herbarium', 'individual_link_decorator', 'collector', 'collection_date', 'specimen_type',
        'label_link_decorator',
    )
    list_filter = (
        'herbarium',
        'specimen_type',
        ('collector__username', ForeignKeyFilter),
        ('herbarium__name', ForeignKeyFilter),
        ('individual__id_name_generated', ForeignKeyFilter),
        ("created_by__username", ForeignKeyFilter),
        ("modified_by__username", ForeignKeyFilter),
    )
    blacklist = ('id', '__str__')

    def get_actions(self, request):
        actions = super().get_actions(request)
        add_label_mass_actions(request, actions, "herbarium_specimen")
        return actions
