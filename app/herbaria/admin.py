from django.contrib import admin
from django.contrib.admin.decorators import register
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django import forms
from django.db import transaction

from .models import *

from tools import readOnlyAdmin
from tools.search_fields import search_fields_compatible
from config_tables.admin import ConfigurableTable, ForeignKeyFilter
from ajax.autocomplete import AutoCompleteForm
from labels.mass_action import add_label_mass_actions


@register(Herbarium)
class HerbariumAdmin(readOnlyAdmin.ReadPermissionModelAdmin, ConfigurableTable):
    form = AutoCompleteForm(Herbarium)
    list_display = (
        'change_link_decorator', 'name', 'comment',
    )
    blacklist = ('id', )


from individuals.models import Individual
@register(HerbariumSpecimen)
class HerbariumSpecimenAdmin(readOnlyAdmin.ReadPermissionModelAdmin, ConfigurableTable):
    form = AutoCompleteForm(HerbariumSpecimen)
    list_display = (
        'change_link_decorator',
        'herbarium', 'individual', 'legato', 'collection_date', 'specimen_type', 'comment',
    )
    list_filter = (
        'herbarium',
        'specimen_type',
        ('legato__username', ForeignKeyFilter),
        ('herbarium__name', ForeignKeyFilter),
        ('individual__id_name_generated', ForeignKeyFilter),
    )
    blacklist = ('id', )

