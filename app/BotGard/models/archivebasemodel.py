from django.db import models
from django.utils.translation import gettext_lazy as _


class ArchiveBaseModel(models.Model):
    """
    Base class for all models that are not deletable and will only
    be flagged as `is_deleted` and not displayed with normal user permissions.

    ModelAdmin must be based on `BotGard.archiveadmin.ArchiveModelAdmin`

    Instantiate the model like this:

        class MyModel(ArchiveBaseModel):
            class Meta:
                permissions = (
                    ("show_deleted_mymodel", _("Show deleted MyModels")),
                )

    The permission allows to show deleted objects in the changelist
    """

    class Meta:
        abstract = True

    is_deleted = models.BooleanField(
        verbose_name=_("Deleted"),
        default=False,
    )

    date_deleted = models.DateTimeField(
        verbose_name=_("Deletion date"),
        null=True, blank=True, default=None,
    )
