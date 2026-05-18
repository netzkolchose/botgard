from django.db import models
from django.utils.translation import gettext_lazy as _


class ArchiveBaseModel(models.Model):
    """
    Base class for all models that are not deletable and will only
    be flagged as `is_deleted` and not displayed with normal user permissions.

    ModelAdmin must be based on `BotGard.archiveadmin.ArchiveModelAdmin`
    """

    class Meta:
        abstract = True

    is_deleted = models.BooleanField(
        verbose_name=_("Archived"),
        default=False,
    )

    date_deleted = models.DateField(
        verbose_name=_("Deletion date"),
        null=True, blank=True, default=None,
    )
