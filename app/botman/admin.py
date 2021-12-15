from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.utils.translation import gettext_lazy as _

from config_tables.admin import ConfigurableTable, configurable, ForeignKeyFilter
from tools import readOnlyAdmin
from .models import *
from labels.mass_action import add_label_mass_actions


if 0:
    # TODO, nice filterable view on user actions, but should really be read-only
    class LogEntryAdmin(ConfigurableTable):
        list_display = ("action_time", "user", "action_flag", "change_message",
                        "content_type", "object_id", "object_repr")
        ordering = ("-action_time",)

    admin.site.register(LogEntry, LogEntryAdmin)


class ExternalCatalogInline(admin.TabularInline):
    model = ExternalCatalog
    fields = ("date_uploaded", "date_outgoing", "file", )
    extra = 0


class OutgoingOrdersInline(admin.TabularInline):
    model = OutgoingOrder
    fields = ("order_text", )
    extra = 0

    # only display unprocessed orders
    def get_queryset(self, request):
        qset = super().get_queryset(request)
        return qset.filter(processed=False)


class BotanicGardenAdmin(readOnlyAdmin.ReadPermissionModelAdmin, ConfigurableTable):
    form = BotanicGardenForm
    list_display = ('change_link_decorator', #'number',
                    'name', 'code', 'phone',
                    'website_link_decorator', 'email_link_decorator', 'label_link_decorator',
                    'delete_link_decorator')
    blacklist = ("id", "__str__", "website", "email")

    search_fields = ['number', 'name', 'code', 'address']

    fieldsets = (
        (None, {
            'fields': ('number', ('name', 'code',), 'address', ('phone', 'website', 'email',), )
        }),
    )
    ordering = ('number',)
    inlines = (ExternalCatalogInline, OutgoingOrdersInline)

    class Media:
        css = {"screen": ('BotGard/css_dropdown/css_dropdown.css',)}

    def get_actions(self, request):
        actions = super().get_actions(request)
        add_label_mass_actions(request, actions, "garden")
        return actions

    def save_formset(self, request, form, formset, change):
        # attach user to OutgoingOrder
        if formset.model == OutgoingOrder:
            instances = formset.save(commit=False)
            for obj in formset.deleted_objects:
                obj.delete()
            for instance in instances:
                instance.user = request.user
                instance.save()
            formset.save_m2m()
        else:
            super().save_formset(request, form, formset, change)

    change_form_template = "botman/garden-change-form.html"


admin.site.register(BotanicGarden, BotanicGardenAdmin)


class ExternalCatalogAdmin(readOnlyAdmin.ReadPermissionModelAdmin, ConfigurableTable):
    form = ExternalCatalogForm
    list_display = (
        "__str__",
        "garden_link_decorator",
        "date_uploaded", "date_outgoing", "file",
        "num_orders_decorator",
        #"delete_link_decorator"
    )
    list_filter = (
        ("garden__full_name_generated", ForeignKeyFilter),
        ("garden__num_orders_generated", ForeignKeyFilter),
    )
    ordering = ("-date_uploaded", )
    blacklist = ("garden", )

admin.site.register(ExternalCatalog, ExternalCatalogAdmin)


class OutgoingOrderAdmin(ConfigurableTable):
    form = OutgoingOrderForm
    list_display = (
        "__str__", "garden_link_decorator",  # "garden_email_decorator",
        "catalog_date", "date_created",
        "user", "user_email_decorator",
        "order_text", "processed",
    )
    list_filter = (
        ("garden__full_name_generated", ForeignKeyFilter),
        ("user__username", ForeignKeyFilter),
    )
    actions = ("mark_orders_as_processed", )

    blacklist = (
        "garden",  # we rather show the change-link decorator
    )

    @admin.action(
        description=_('Mark orders as processed'),
        permissions=("mark_as_processed", ),
    )
    def mark_orders_as_processed(self, request, queryset):
        self.message_user(
            request,
            _("%(num_orders)s orders have been marked as processed") % {
                "num_orders": queryset.count(),
            }
        )
        queryset.update(processed=True)
        # update the BotanicGarden.num_orders_generated field
        for garden_pk in queryset.values_list("garden", flat=True).distinct():
            BotanicGarden.objects.get(pk=garden_pk).save()

    def has_mark_as_processed_permission(self, request):
        # Only catalog maintainers can mark orders as processed
        return request.user.has_perm("botman.add_externalcatalog")

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        form.base_fields['user'].initial = request.user.pk
        return form


admin.site.register(OutgoingOrder, OutgoingOrderAdmin)


# TODO-3: maybe override AdminSite and use in each app
#   (https://docs.djangoproject.com/en/3.1/ref/contrib/admin/#customizing-the-adminsite-class)
admin.site.enable_nav_sidebar = False
admin.site.index_title = "BotGard"  # text above admin index page
admin.site.site_title = " "  # The actual title will be "index_title | site_title" so this isn't perfect
admin.site.site_url = None  # Disable VIEW SITE link
