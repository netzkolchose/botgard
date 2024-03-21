import traceback

from django.db import transaction
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from botman.models import ExternalCatalog, ExternalCatalogArchive


def move_catalogs_to_archive(admin, request, queryset):
    try:
        with transaction.atomic():
            pks = list(queryset.values_list("pk", flat=True))

            for pk in pks:
                catalog: ExternalCatalog = ExternalCatalog.objects.get(pk=pk)
                archived_catalog = ExternalCatalogArchive.objects.create(
                    garden=catalog.garden,
                    date_uploaded=catalog.date_uploaded,
                    date_outgoing=catalog.date_outgoing,
                    file=catalog.file,
                )
                catalog.delete()

            admin.message_user(
                request,
                _("Moved %s catalogs to archive") % len(pks),
                level=messages.INFO,
            )

    except Exception as e:
        admin.message_user(
            request,
            _("Error moving catalogs: %s") % f"{type(e).__name__}: {e}",
            level=messages.ERROR,
        )
        traceback.print_exc()
