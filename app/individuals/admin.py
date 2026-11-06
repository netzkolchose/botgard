import re
from typing import List, Type

from django.contrib import admin
from django.http import QueryDict
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django import forms
from django.db import transaction
from django.urls import reverse
from django.core.exceptions import PermissionDenied

from config_app.forms import CustomPropertyTabularInline
from tools.fieldsets import remove_from_fieldsets
from tools.permissions import check_user_has_permissions, check_user_has_any_permissions
from .models import *
from plantimages.admin import PlantImageInline

from tools.search_fields import search_fields_compatible
from config_tables.admin import ConfigurableTable, ForeignKeyFilter
from ajax.autocomplete import AutoCompleteForm
from labels.mass_action import add_label_mass_actions
from herbaria.models.specimen import HerbariumSpecimen, create_herbarium_specimen_form_class
from .actions import add_seed_catalog_actions
from .models.individual import SeedInLatestCatalogFilter
from geo.columns import MAP_COLUMN_CSS, MAP_COLUMN_JS


class DepartmentAdmin(ConfigurableTable):

    form = DepartmentForm
    list_display = ('change_link_decorator', 'territory', 'code', 'name', 'list_link_decorator',
                    'num_individuals_alive', 'num_species_alive',
                    'delete_link_decorator',
                    )
    list_display_links = ()
    list_filter = (
        ('territory__name_generated', ForeignKeyFilter),
        ("created_by__username", ForeignKeyFilter),
        ("modified_by__username", ForeignKeyFilter),
    )
    search_fields = search_fields_compatible(('code', 'name'))
    ordering = ("territory__code", 'code')
    admin_order_field = ("territory__code", "code")
    blacklist = ("id", "__str__",)

    change_form_template = "individuals/change_form_plant_stats.html"
    change_list_template = "individuals/change_list_edit_map.html"

    # TODO: just an idea how to generically add extra action buttons,
    #   however, the changelist_view code would need to be adjusted and
    #   change_list_template must be overridden in a clever way to
    #   keep all the extras that the derrived ModelAdmin class might have already done
    # def extra_action_buttons(self):
    #     return [
    #        {"name": _("Garden map"), "url": reverse("geo:garden_map")},
    #     ]

    class Media:
        css = {"screen": ('individuals/change_form_plant_stats.css',)}


class TerritoryAdmin(ConfigurableTable):
    form = TerritoryForm
    list_display = ('change_link_decorator', 'code', 'name', 'list_link_decorator',
                    'num_individuals_alive', 'num_species_alive',
                    'delete_link_decorator')
    list_display_links = ()
    search_fields = search_fields_compatible(('code', 'name'))
    ordering = ('code',)
    blacklist = ("id", "name_generated", )
    list_filter = (
        ("created_by__username", ForeignKeyFilter),
        ("modified_by__username", ForeignKeyFilter),
    )

    change_form_template = "individuals/change_form_plant_stats.html"
    change_list_template = "individuals/change_list_edit_map.html"

    class Media:
        css = {"screen": ('individuals/change_form_plant_stats.css',)}


class OutplantingInline(admin.TabularInline):
    form = OutplantingForm
    model = Outplanting
    fields = (
        "department", "location", "seeded_date", "date", "inventory_date", "plant_died", "comment",
    )
    min_num = 0
    extra = 0


class HerbariumSpecimenInline(admin.TabularInline):
    form = create_herbarium_specimen_form_class(
        # remove one of the defaults, otherwise user might click "add specimen"
        # and all defaults might be exactly the ones the user wants to enter
        # and nothing is saved, because django thought nothing was entered
        no_default_specimen_type=True,
        widgets={
            "comment": forms.TextInput,  # don't use textarea in inline form
        }
    )
    model = HerbariumSpecimen
    min_num = 0
    extra = 0
    fields = ("herbarium", "collector", "collection_date", "specimen_type", "comment")


class IndividualAdminMixin:

    def save_form(self, request, form: forms.Form, change: bool):
        """
        Override to store Individual.species_audit
        """
        instance = super().save_form(request, form, change)
        if instance.species_audit == '':
            instance.species_audit = None
        try:
            original_instance = Individual.objects.get(pk=instance.pk)
            instance.add_species_audit(original_instance)
        except Individual.DoesNotExist:
            pass
        return instance

    def save_formset(self, request, form, formset: forms.BaseFormSet, change: bool):
        """
        Override to store Individual.outplanting_audit
        """
        old_outplantings_data = None
        if formset.model is Outplanting and form.instance:
            old_outplantings_data = form.instance.get_outplantings_data()

        super().save_formset(request, form, formset, change)

        if old_outplantings_data is not None:
            form.instance.store_outplantings_audit(old_outplantings_data)


    def get_fieldsets(self, request, obj=None):
        """
        Override to
        - remove the display of `species_audit` if nothing is there
        """
        fieldsets = super().get_fieldsets(request, obj)

        if not obj or not obj.species_audit:
            fieldsets = remove_from_fieldsets(fieldsets, "species_audit")

        return fieldsets


class IndividualAdmin(IndividualAdminMixin, ConfigurableTable):
    change_form_template = "individuals/change_form_individual.html"
    object_history_template = "individuals/object_history.html"
    form = IndividualForm
    save_on_top = True
    list_display = (
        'change_link_decorator', 'accession_number',
        #'accession_extension',
        'ipen_generated',
        #'sowing_number',
        'species_link_decorator',
        'departments_decorator', 'is_alive', 'source', 'etikett_link_decorator',
    )
    list_filter = (
        # add all foreignkey fields that should be filterable
        ('user__username', ForeignKeyFilter),
        ('source__full_name_generated', ForeignKeyFilter),
        ('species__full_name_generated', ForeignKeyFilter),
        ('species__nomenclature_checked', ForeignKeyFilter),
        ('species__protection_of_species', ForeignKeyFilter),
        ('species__area_of_distribution_etikettxt', ForeignKeyFilter),
        ('species__area_of_distribution_background', ForeignKeyFilter),
        ('species__family__family', ForeignKeyFilter),
        ('species__family__genus', ForeignKeyFilter),
        ('literature__full_name_generated', ForeignKeyFilter),
        ('projects__full_name_generated', ForeignKeyFilter),
        ("created_by__username", ForeignKeyFilter),
        ("modified_by__username", ForeignKeyFilter),
    )

    blacklist = ('id', '__str__', 'ipen_transfer_restricted', 'ipen_garden_code', 'ipen_accession_number',
                 'ipen_country', 'departments_generated', 'territories_generated', 'species',
                 'outplantings_generated', 'alive_outplantings_generated', 'is_alive_generated',
                 'species_audit', 'found_coordinates')

    list_display_links = ()
    search_fields = search_fields_compatible((
        'accession_number',
        'ipen_generated',
        '@came_as_species',
        '@species__species',
        '@species__subspecies',
        '@species__variety',
        '@species__form',
        '@species__family__genus',
        '@species__family__family',
        '@species__full_name_generated',
        '@species__deutscher_name',
        '@species__synonyme',
        '@source__name',
    ))
    ordering = ('accession_number',)
    fieldsets = (
        (None, {
            'fields': (
                ('accession_number', 'accession_extension', 'seed_available', 'seed_in_stock',),
                ('species', 'species_checked_by', 'species_checked_date', 'came_as_species'),
                'species_comment',
                'literature',
                'species_audit',
            )
        }),
        ('IPEN', {
            'fields': (('ipen_country', 'ipen_transfer_restricted', 'ipen_garden_code', 'ipen_accession_number'),)
        }),
        (_('habitat'), {
            'fields': (
                'found_country',
                ('found_text', 'found_coordinates'),
                ('collector_name', 'collector_number', 'collector_date'),
            )
        }),
        (_('source'), {
            'fields': (('source', 'source_date', 'came_in_as', 'external_order_number'),)
        }),
        (_('miscellaneous'), {
            'fields': (
                'gender', 'comment',
                'projects',
                'import_reference', 'status'
            )
        }),
        (_('seeds'), {
            'fields': ('order_number', 'sowing_number')
        })
    )
    raw_id_fields = ("species",)
    inlines = [OutplantingInline, PlantImageInline, HerbariumSpecimenInline]

    class Media:
        css = {"screen": (
            "BotGard/css_dropdown/css_dropdown.css",
            "individuals/outplanting-inline.css",
            *MAP_COLUMN_CSS,
        )}
        js = (
            "individuals/change_form_tools.js",
            *MAP_COLUMN_JS,
        )

    def get_actions(self, request):
        actions = super().get_actions(request)
        add_label_mass_actions(request, actions, "individual")
        return actions

    # ---- allow change to Outplanting inlines even if no change-permission to Individual ----

    def has_outplanting_change_permission(self, request) -> bool:
        return check_user_has_any_permissions(
            request.user,
            "individuals.change_outplanting",
            "individuals.add_outplanting"
        )

    def has_outplanting_add_permission(self, request) -> bool:
        return check_user_has_permissions(request.user, "individuals.add_outplanting")

    def get_inline_formsets(self, request, formsets, inline_instances, obj=None):
        """Override to set OutplantingInlineFormSet.has_change_permission=True"""
        from django.contrib.admin.helpers import InlineAdminFormSet
        formsets: List[InlineAdminFormSet] = super().get_inline_formsets(request, formsets, inline_instances, obj)
        if self.has_outplanting_change_permission(request):
            for fs in formsets:
                if fs.formset.model is Outplanting:
                    fs.has_change_permission = True
                    if self.has_outplanting_add_permission(request):
                        fs.has_add_permission = True
                        fs.formset.max_num = 1000
        return formsets

    def save_related(self, request, form, formsets, change):
        """Override to allow saving OutplantingInlineFormSet and skip all the rest if no Individual change permission"""
        if super().has_change_permission(request):
            return super().save_related(request, form, formsets, change)
        else:
            if not self.has_outplanting_change_permission(request):
                raise PermissionDenied
            else:
                # Don't save self (form) and only save Outplanting formset
                for formset in formsets:
                    if formset.model is Outplanting:
                        self.save_formset(request, form, formset, change=change)
                    else:
                        formset.new_objects = []
                        formset.changed_objects = []
                        formset.deleted_objects = []

    def _changeform_view(self, request, object_id, form_url, extra_context):
        """
        Override to allow saving OutplantingInlineFormSet and skip all the rest if no Individual change permission
        """
        # go to orignal _changeform_view ...
        if (
                request.method != "POST"
                or "_saveasnew" in request.POST
                or self.has_change_permission(request)
                or self.has_add_permission(request)
        ):
            return super()._changeform_view(request, object_id, form_url, extra_context)

        # or allow access if indi-view AND outplanting_change/add_permission
        if not (
                self.has_view_permission(request)
                and self.has_outplanting_change_permission(request)
        ):
            raise PermissionDenied

        # -- Below is copied from Django 5.2 contrib/admin/options.py with some adjustments --
        # (does NEVER save the Individual, only the related Outplantings)

        from django.contrib.admin.options import (
            TO_FIELD_VAR, IS_POPUP_VAR, DisallowedModelAdminToField, unquote, flatten_fieldsets,
            all_valid, helpers,
        )
        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        if to_field and not self.to_field_allowed(request, to_field):
            raise DisallowedModelAdminToField(
                "The field %s cannot be referenced." % to_field
            )

        obj = self.get_object(request, unquote(object_id), to_field)
        if obj is None:
            return self._get_obj_does_not_exist_redirect(
                request, self.opts, object_id
            )

        fieldsets = self.get_fieldsets(request, obj)
        ModelForm = self.get_form(
            request, obj, change=True, fields=flatten_fieldsets(fieldsets)
        )

        form = ModelForm(request.POST, request.FILES, instance=obj)
        formsets, inline_instances = self._create_formsets(
            request,
            form.instance,
            change=True,
        )
        if all_valid(formsets):
            self.save_related(request, form, formsets, change=True)
            change_message = self.construct_change_message(
                request, forms.Form(), formsets, add=False,
            )
            self.log_change(request, obj, change_message)
            return self.response_change(request, obj)

        readonly_fields = flatten_fieldsets(fieldsets)
        #else:
        #    readonly_fields = self.get_readonly_fields(request, obj)
        admin_form = helpers.AdminForm(
            form,
            list(fieldsets),
            {},
            readonly_fields,
            model_admin=self,
        )
        media = self.media + admin_form.media

        inline_formsets = self.get_inline_formsets(
            request, formsets, inline_instances, obj
        )
        for inline_formset in inline_formsets:
            media += inline_formset.media

        title = _("View %s")
        context = {
            **self.admin_site.each_context(request),
            "title": title % self.opts.verbose_name,
            "subtitle": str(obj) if obj else None,
            "adminform": admin_form,
            "object_id": object_id,
            "original": obj,
            "is_popup": IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET,
            "to_field": to_field,
            "media": media,
            "inline_admin_formsets": inline_formsets,
            "errors": helpers.AdminErrorList(form, formsets),
            "preserved_filters": self.get_preserved_filters(request),
        }

        context.update(extra_context or {})

        return self.render_change_form(
            request, context, add=False, change=True, obj=obj, form_url=form_url
        )


class SeedAdmin(IndividualAdminMixin, ConfigurableTable):
    form = SeedForm
    save_on_top = True
    actions_on_top = True
    list_display = (
        'change_link_decorator', 'order_number', 'accession_number', 'accession_extension', 'ipen_generated',
        'species_link_decorator', 'seed_available', 'seed_in_stock', 'seed_add_to_latest_catalog_decorator',
        'seed_etikett_decorator', 'endangering_decorator')
    list_filter = (
        *IndividualAdmin.list_filter,
        (SeedInLatestCatalogFilter.QUERY_NAME, SeedInLatestCatalogFilter),
    )

    blacklist = IndividualAdmin.blacklist

    search_fields = (
        'order_number',
        *IndividualAdmin.search_fields,
    )
    ordering = IndividualAdmin.ordering
    list_editable = ('seed_available', 'seed_in_stock')
    fieldsets = remove_from_fieldsets(IndividualAdmin.fieldsets, "found_coordinates")
    raw_id_fields = IndividualAdmin.raw_id_fields

    class Media:
        css = {"screen": (
            'BotGard/css_dropdown/css_dropdown.css',
            'BotGard/css/no-changelist-filter-box.css',
        )}
        js = (
            "individuals/change_form_tools.js",
        )

    def get_search_results(self, request, queryset, search_term):
        order_ids = get_seed_order_ids(search_term)
        if not order_ids:
            return super().get_search_results(request, queryset, search_term)

        return queryset.filter(order_number__in=order_ids), False

    def get_actions(self, request):
        actions = {}
        add_seed_catalog_actions(request, actions)
        add_label_mass_actions(request, actions, "individual")
        actions.update(super().get_actions(request))
        return actions


def get_seed_order_ids(s: str) -> List[str]:
    return re.findall(r"\d+", s)


admin.site.register(Individual, IndividualAdmin)
admin.site.register(Seed, SeedAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Territory, TerritoryAdmin)


# ------- below is for transfer from entrybook.Entry to inidividuals.Individual and Outplanting ------


class OutplantingAlwaysChangedForm(OutplantingForm):
    """
    ModelForm for Outplanting inline to mark
    the initial data from entrybook.Entry as changed.
    """
    def has_changed(self):
        return bool(self.initial.get("department"))


class OutplantingAlwaysChangedInline(OutplantingInline):
    form = OutplantingAlwaysChangedForm


class IndividualFromEntryAdmin(IndividualAdmin):
    """
    Special ModelAdmin that creates an
    Individual form and formsets
    from an entrybook.models.Entry instance
    """
    inlines = [OutplantingAlwaysChangedInline, PlantImageInline]

    def __init__(self, model, admin_class, entry_pk):
        from entrybook.models import Entry

        super().__init__(model, admin_class)
        self._entry_pk = entry_pk
        self._entry = Entry.objects.get(pk=self._entry_pk)

    def get_changeform_initial_data(self, request):
        """
        Set the initial values for Individual Form from the Entry instance.
        (not including inline FormSets)
        """
        entry_values = {
            field.name: getattr(self._entry, field.name)
            for field in self._entry._meta.fields
            if hasattr(Individual, field.name)
        }
        entry_values["projects"] = list(self._entry.projects.all().values_list("pk", flat=True))
        return entry_values

    def get_form(self, request, obj=None, change=False, **kwargs):
        """
        Return a Form class that does NOT initialize the
        accession number. It's already stored in the Entry instance
        """
        Form = super().get_form(request, obj, change, **kwargs)

        class PatchedForm(Form):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs, do_not_initialize_accession=True)

        return PatchedForm

    def get_formsets_with_inlines(self, request, obj=None):
        """
        Replace the FormSet class for the OutplantingInline
        with a class that initializes all values
        """
        from django.forms import BaseModelFormSet

        for form_set_class, inline_instance in super().get_formsets_with_inlines(request, obj):
            form_set_class: Type[BaseModelFormSet]
            if isinstance(inline_instance, OutplantingInline):
                entry = self._entry
                if entry.department:

                    class PatchedFormSet(form_set_class):
                        min_num = 1
                        def __init__(self, *args, **kwargs):
                            kwargs["initial"] = [{
                                "department": str(entry.department.pk) if entry.department else None,
                                "seeded_date": entry.seeded_date,
                                "date": entry.bed_out_date,
                            }]
                            super().__init__(*args, **kwargs)

                        def has_changed(self):
                            return True

                    form_set_class = PatchedFormSet

            yield form_set_class, inline_instance


class OutplantingAdmin(ConfigurableTable):
    form = OutplantingForm
    list_display = (
        'change_link_decorator',
        'territory_decorator', 'department_decorator',
        'seeded_date', 'date', 'plant_died',
        'individual_link_decorator', 'family_single', 'genus_single',
    )
    list_filter = (
        ('department__code', ForeignKeyFilter),
        ('department__territory__code', ForeignKeyFilter),
        ('individual__ipen_generated', ForeignKeyFilter),
        ('individual__species__family__family', ForeignKeyFilter),
        ('individual__species__family__genus', ForeignKeyFilter),
        ("created_by__username", ForeignKeyFilter),
        ("modified_by__username", ForeignKeyFilter),
    )
    blacklist = ('id', 'individual', 'department', 'location')

    class Media:
        css = {"screen": (
            "BotGard/css_dropdown/css_dropdown.css",
            *MAP_COLUMN_CSS,
        )}
        js = (
            *MAP_COLUMN_JS,
        )

    def get_actions(self, request):
        actions = super().get_actions(request)
        add_label_mass_actions(request, actions, "outplanting")
        return actions


admin.site.register(Outplanting, OutplantingAdmin)

