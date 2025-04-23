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

from tools import readOnlyAdmin
from tools.search_fields import search_fields_compatible
from config_tables.admin import ConfigurableTable, ForeignKeyFilter
from labels.mass_action import add_label_mass_actions

from .models import *


class EntryAdmin(readOnlyAdmin.ReadPermissionModelAdmin, ConfigurableTable):
    form = EntryForm
    save_on_top = True

    list_display = (
        'change_link_decorator',
        'user', 'department_decorator',
        'accession_number', 'accession_extension', 'ipen_generated',
        'sowing_number',
        'source', 'etikett_link_decorator',
    )

    blacklist = (
        'id', '__str__',
        'ipen_transfer_restricted', 'ipen_garden_code', 'ipen_accession_number', 'ipen_country',
        'department',
    )

    list_display_links = ()
    search_fields = search_fields_compatible((
        'accession_number',
        'ipen_generated',
        '@species',
        'source',
        'came_in_as',
        'sowing_number',
        'order_number',
    ))
    list_filter = (
        ("user__username", ForeignKeyFilter),
        ("department__code", ForeignKeyFilter),
    )

    ordering = ('accession_number',)

    fieldsets = (
        (None, {
            'fields': (
                ('accession_number', 'accession_extension', 'seed_available', 'seed_in_stock',),
                ('species', 'species_checked_by', 'came_as_species'),
                ('user',),
            )
        }),
        (_('source'), {
            'fields': (
                ('source', 'external_order_number'),
                ('source_date', 'came_in_as'),
            )
        }),
        ('IPEN', {
            'fields': (('ipen_country', 'ipen_transfer_restricted', 'ipen_garden_code', 'ipen_accession_number'),)
        }),
        (_('habitat'), {
            'fields': (('found_country',), 'found_text', ('collector_name', 'collector_number', 'collector_date'),)
        }),
        (_('miscellaneous'), {
            'classes': 'collapse',
            'fields': ('gender', 'comment',)
        }),
        (_('seeds'), {
            'fields': ('order_number', 'sowing_number')
        }),
        (_('Outplanting'), {
            'fields': (('department', 'seeded_date', 'bed_out_date'), )
        }),
    )

    class Media:
        css = {"screen": ('BotGard/css_dropdown/css_dropdown.css',)}

    def get_actions(self, request):
        actions = super().get_actions(request)
        add_label_mass_actions(request, actions, "entry")
        return actions

    def get_form(self, request, obj=None, change=False, **kwargs):
        """
        Pre-fill `user` field
        """
        form = super().get_form(request, obj, change, **kwargs)
        form.base_fields['user'].initial = request.user.pk
        return form

    def get_urls(self):
        """
        Add the save-as-individual url
        """
        urls = super().get_urls()
        admin_site = self.admin_site
        opts = self.model._meta
        info = opts.app_label, opts.model_name
        return urls + [
            re_path(
                r"^save-as-individual/(?P<pk>\d+)/?$",
                admin_site.admin_view(self.save_as_individual_view),
                name='%s_%s_save_as_individual' % info,
            )
        ]

    #def save_model(self, request, obj, form, change):
    #    obj.user = request.user
    #    super().save_model(request, obj, form, change)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        Handle save-as-individual button
        """
        # try to save the model
        response = super().change_view(request, object_id, form_url, extra_context)

        # always return the response on form errors
        if isinstance(response, TemplateResponse):
            if response.context_data.get("errors"):
                return response

        # redirect to patched individual change_view
        #   (because we need to do a GET on the change_view)
        if "_saveasindividual" in request.POST:
            return HttpResponseRedirect(
                reverse("admin:entrybook_entry_save_as_individual", args=(object_id, ))
            )

        return response

    def save_as_individual_view(self, request, pk, extra_context=None):
        """
        Patched Individual change_view

        This renders the change_view for Individual but using
        the special IndividualFromEntryAdmin ModelAdmin which
        initializes all Individual fields from the Entry fields
        """
        from individuals.admin import IndividualFromEntryAdmin
        from individuals.models import Individual

        model_admin = IndividualFromEntryAdmin(Individual, self.admin_site, entry_pk=pk)
        return model_admin.change_view(request, None, extra_context=extra_context)


admin.site.register(Entry, EntryAdmin)
