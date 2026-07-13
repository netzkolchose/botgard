import traceback
from typing import List, Tuple, Union

import rapidfuzz

from django.db import transaction
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from botman.models import ExternalCatalog, ExternalCatalogArchive, BGCIGarden


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


def fuzzy_find_bgci_garden(
        term: str,
        max_num: int = 10,
        keys: Tuple[str] = ("name", "city"),
        with_scores: bool = False,
) -> Union[List[BGCIGarden], List[Tuple[BGCIGarden, float]]]:
    """
    Find a BGCI garden by fuzzy-matching against `BGCIGarden.<key>`

    The score for each key is summed and the highest `max_num` BGCIGarden instances are returned.
    """
    bgci_data = list(BGCIGarden.objects.all().values("pk", *keys))

    scores = {}
    for scorer in (
            rapidfuzz.fuzz.ratio,
            rapidfuzz.fuzz.partial_ratio,
    ):
        for key in keys:
            for data, score in zip(
                    bgci_data,
                    rapidfuzz.process.cdist(
                        [term.lower()],
                        [(i[key] or "").lower() for i in bgci_data],
                        scorer=scorer,
                    )[0]
            ):
                scores[data["pk"]] = scores.get(data["pk"], 0) + score

    pks_sorted = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)

    result = [
        BGCIGarden.objects.get(pk=pk)
        for pk in pks_sorted[:max_num]
    ]

    if with_scores:
        result = [(g, float(scores[g.pk])) for g in result]

    return result
