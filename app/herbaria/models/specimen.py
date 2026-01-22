from django.db import models, OperationalError
from django import forms
from django.forms import widgets
from django.forms.utils import ErrorList
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy as __
from django.urls import reverse
from django.templatetags.static import static
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
#from django.db.models.signals import post_save
#from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model

from config_tables.admin import configurable, Configurable
from ajax.autocomplete import AutoCompleteForm
from tools.global_request import get_current_user


HERBARIUM_SPECIMEN_TYPES = (
    ("plant_generative", _("Plant (generative)")),
    ("plant_vegetative", _("Plant (vegetative)")),
    ("blossoms", _("Blossoms")),
    ("leaves", _("Leaves")),
    ("fruits", _("Fruits")),
)

def get_default_herbarium():
    """
    Return (in this priority):
    - the Herbarium used for the latest created HerbariumSpecimen
    - the first created Herbarium
    - None
    """
    from .herbarium import Herbarium

    newest_specimen = HerbariumSpecimen.objects.all().order_by("-pk").first()
    if newest_specimen is not None:
        return newest_specimen.herbarium

    return Herbarium.objects.all().order_by("pk").first()


class HerbariumSpecimen(Configurable, models.Model):

    class Meta:
        verbose_name = _("Specimen")
        verbose_name_plural = _("Specimens")

    herbarium = models.ForeignKey(
        to="herbaria.Herbarium",
        on_delete=models.CASCADE,
        db_index=True,
        default=get_default_herbarium,
        related_name="specimens",
    )

    individual = models.ForeignKey(
        to="individuals.Individual",
        on_delete=models.CASCADE,
        db_index=True,
        related_name="herbarium_specimens",
    )

    collector = models.ForeignKey(
        verbose_name="Legato",
        help_text=_("Collector"),
        to=get_user_model(),
        on_delete=models.CASCADE,
        default=get_current_user,
        db_index=True,
        related_name="herbarium_collectors",
    )

    collection_date = models.DateField(
        auto_now_add=True,
    )

    specimen_type = models.CharField(
        verbose_name=_("Specimen type"),
        choices=HERBARIUM_SPECIMEN_TYPES,
        default=HERBARIUM_SPECIMEN_TYPES[0][0],
        max_length=32,
        db_index=True,
    )

    comment = models.TextField(
        verbose_name=_("Comment"),
        null=True, blank=True,
        db_index=True,
    )

    @configurable
    def __str__(self):
        return _("Specimen of {}").format(self.individual.id_name_generated)

    __str__.admin_order_field = 'individual.id_name_generated'
    __str__.short_description = _('Specimen')

    @configurable
    def change_link_decorator(self):
        return _("show")

    change_link_decorator.short_description = _("show")
    change_link_decorator.exclude_csv = True

    @configurable
    def delete_link_decorator(self):
        url = reverse("admin:herbaria_herbariumspecimen_delete", args=(self.pk,))
        return mark_safe('<a href="%s" class="deletelink">%s</a>' % (url, _("delete")))

    delete_link_decorator.short_description = _("delete")
    delete_link_decorator.exclude_csv = True

    @configurable
    def label_link_decorator(self):
        from labels import label_link_decorator
        return label_link_decorator(
            "herbarium", self.pk, filename=f"specimen-{self.pk}"
        )

    label_link_decorator.short_description = _("create label")
    label_link_decorator.exclude_csv = True


def create_herbarium_specimen_form_class(**autocomplete_kwargs):
    class HerbariumSpecimenForm(AutoCompleteForm(HerbariumSpecimen, **autocomplete_kwargs)):
        exclude_autocomplete = (
            # There will be only one or a few herbaria, make it more simple to select without typing
            "herbarium",
            # Users are filtered to active users, so don't use autocomplete
            "collector",
        )
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["collector"].queryset = (
                get_user_model()
                .objects.filter(is_active=True, is_staff=True)
                .order_by("username")
            )
    return HerbariumSpecimenForm
