from django.utils.translation import gettext_lazy as _
from django.contrib.admin import ModelAdmin
from django.db.models import QuerySet
from django.db import transaction
from django.contrib import messages

from seedcatalog.models import SeedCatalog
from individuals.models import Seed


def add_seed_catalog_actions(request, actions: dict):
    if not SeedCatalog.objects.latest_editable_catalog():
        return

    action_name = "add_seeds_to_current_catalog"
    actions[action_name] = (
        _action_seeds_to_catalog,
        action_name,
        _("Add select seeds to current catalog"),
    )
    action_name = "remove_seeds_from_current_catalog"
    actions[action_name] = (
        _action_seeds_remove_from_catalog,
        action_name,
        _("Remove select seeds from current catalog"),
    )


def _action_seeds_to_catalog(admin: ModelAdmin, request, queryset: QuerySet):
    catalog = SeedCatalog.objects.latest_editable_catalog()
    if not catalog:
        admin.message_user(request, _('Seed catalog not found'), messages.ERROR)
        return

    num_added = 0

    with transaction.atomic():
        for seed in queryset:
            if not catalog.seed.contains(seed):
                num_added += 1
                catalog.seed.add(seed)
                if not seed.seed_available:
                    seed.seed_available = True
                    seed.save()

    admin.message_user(request, _('{} seeds added to {}').format(num_added, catalog))


def _action_seeds_remove_from_catalog(admin: ModelAdmin, request, queryset: QuerySet):
    catalog = SeedCatalog.objects.latest_editable_catalog()
    if not catalog:
        admin.message_user(request, _('Seed catalog not found'), messages.ERROR)
        return

    num_removed = 0

    with transaction.atomic():
        for seed in queryset:
            if catalog.seed.contains(seed):
                num_removed += 1
                catalog.seed.remove(seed)

    admin.message_user(request, _('{} seeds removed from {}').format(num_removed, catalog))

