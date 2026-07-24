from typing import Optional

from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy as __
from django.contrib.auth import get_user_model
from django.utils import timezone

from species.models import Species
from botman.models import BotanicGarden
from individuals.models.individual_base import *
import config_app


class Entry(IndividualBase(custom_properties_unique_name="entry")):

    class Meta:
        verbose_name = _("Seed/individual entry")
        verbose_name_plural = _("Seed/individual entries")

    _id_field = "id_name_generated"

    # --- override fields to make them optional ---

    ipen_transfer_restricted = models.CharField(
        max_length=1,
        choices=(("", ""),) + IPEN_TRANSFER_RESTRICTIONS,
        verbose_name="-",
        blank=True,
    )

    ipen_country = models.CharField(
        verbose_name="IPEN",
        max_length=3,
        choices=(("", ""),) + ISO_COUNTRY_CHOICES,
        db_index=True,
        blank=True
    )

    found_country = models.CharField(
        verbose_name=_("collecting country"),
        max_length=3,
        choices=(("", ""),) + ISO_COUNTRY_CHOICES,
        db_index=True,
        blank=True
    )

    # --- the following Individual fields are replaced by simple CharFields ---

    # originally FK on species.Species
    species = models.CharField(
        verbose_name=_("genus & Species"),
        max_length=128,
        blank=True,
        db_index=True,
    )

    # originally FK on botman.BotanicGarden
    source = models.CharField(
        verbose_name=_("source"),
        max_length=128,
        blank=True,
        db_index=True,
    )

    # originally FK on botman.BotanicGarden
    ipen_garden_code = models.CharField(
        verbose_name="-",
        max_length=128,
        blank=True,
        db_index=True,
    )

    user = models.ForeignKey(
        verbose_name=_("Created by"),
        to=get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        related_name="entries",
    )

    # ----------- extra fields that are mapped to individuals.models.Outplanting -------------

    seeded_date = models.DateField(
        verbose_name=_("sowing date"),
        null=True, blank=True,
    )

    bed_out_date = models.DateField(
        verbose_name=_("bed out date"),
        null=True, blank=True,
    )

    department = models.ForeignKey(
        verbose_name=_("department"),
        to="individuals.Department",
        on_delete=models.SET_DEFAULT,
        null=True, blank=True, default=None,
    )

    @configurable
    def __str__(self):
        return self.id_name_generated
    __str__.admin_order_field = 'id_name_generated'
    __str__.short_description = _('Seed/individual entry')

    @configurable
    def change_link_decorator(self):
        return _("show")
    change_link_decorator.short_description = _("show")
    change_link_decorator.exclude_csv = True

    @configurable
    def delete_link_decorator(self):
        url = reverse("admin:entrybook_entry_delete", args=(self.pk,))
        return mark_safe('<a href="%s" class="deletelink">%s</a>' % (url, _("delete")))
    delete_link_decorator.short_description = _("delete")
    delete_link_decorator.exclude_csv = True

    @configurable
    def etikett_link_decorator(self):
        from labels import label_link_decorator
        return label_link_decorator(
            "entry", self.pk, filename=self.ipen_generated
        )

    etikett_link_decorator.short_description = _("create label")
    etikett_link_decorator.exclude_csv = True

    @configurable
    def etikett_link_decorator(self):
        from labels import label_link_decorator
        return label_link_decorator(
            "entry", self.pk, self.id_name_generated
        )
    etikett_link_decorator.short_description = _("create label")
    etikett_link_decorator.exclude_csv = True

    @configurable
    def department_decorator(self):
        return "%s" % self.department
    department_decorator.short_description = _("department")
    department_decorator.admin_order_field = "department__code"

    def get_ipen_garden_code(self) -> Optional[str]:
        garden_code = self.ipen_garden_code
        if garden_code:
            garden_code = garden_code.split()[0]
            try:
                garden_number = int(garden_code)
                garden_code = BotanicGarden.objects.get(number=garden_number).code
            except (ValueError, BotanicGarden.DoesNotExist) as e:
                pass
        return garden_code

    def save(self, *args, **kwargs):
        # -- update generated fields --
        self.ipen_generated = generate_entry_ipen(self)

        self.id_name_generated = str(self.accession_number)
        if self.species:
            self.id_name_generated += f" ({self.species})"
        self.id_name_generated = self.id_name_generated[:100]

        super(Entry, self).save(*args, **kwargs)


class EntryForm(
    AutoCompleteForm(
        Entry,
        #widgets={
        #    "accession_number": widgets.NumberInput(),  # don't need a spinbox for the accession number
        #},
        autocomplete_mapping={
            "species": {"model": Species, "field": "full_name_generated"},
            "came_as_species": {"model": Species, "field": "full_name_generated"},
            "source": {"model": BotanicGarden, "field": "full_name_generated"},
            "ipen_garden_code": {"model": BotanicGarden, "field": "full_name_generated"},
            # "department": {"model": Department, "field": "full_code"},
        }
    )
):
    exclude_autocomplete = ("department", )

    def __init__(self, *args, **kwargs):
        if not kwargs.get("instance"):
            kwargs.setdefault("initial", {})
            # create same random accession number in two fields when creating a new individual
            kwargs["initial"]["accession_number"] = kwargs["initial"]["ipen_accession_number"] = (
                get_new_accession_number()
            )

        super(EntryForm, self).__init__(*args, **kwargs)


def _validate_ipen_creation(code):
    from django.forms import ValidationError
    model = Entry(
        ipen_country="XX",
        ipen_transfer_restricted="0",
        ipen_accession_number="1234",
        ipen_garden_code="ABC",
        accession_extension="10",
    )
    model.pk = 1
    try:
        generate_entry_ipen(model, code=code)
    except Exception as e:
        raise ValidationError(f"{type(e).__name__}: {e}")


config_app.register_key(
    "ipen_creation_entry",
    default=""""{}-{}-{}-{}".format(
self.ipen_country.split()[0].upper() if self.ipen_country else "xx",
self.ipen_transfer_restricted.upper() if self.ipen_transfer_restricted else "x",
self.get_ipen_garden_code() or "x",
self.ipen_accession_number or "x",
)""",
    description="A python expression that generates the full IPEN from an Entry. The Entry instance is available as `self`",
    validator=_validate_ipen_creation,
    translateable=False,
)


def generate_entry_ipen(entry: Entry, code=None):
    if code is None:
        code = config_app.get_value("ipen_creation_entry")
    return eval(code, {"self": entry})
