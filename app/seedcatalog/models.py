import os
import datetime
import time

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe


class SeedCatalog(models.Model):
    class Meta:
        verbose_name = _('seed catalog')
        verbose_name_plural = _('seed catalogs')
        permissions = (("can_finalize_catalog", _("can finalize a seed catalog")),)

    _id_field = "release_date"

    # validity and creation dates
    release_date = models.DateField(verbose_name=_('release date'), blank=False, null=False)
    valid_until_date = models.DateField(verbose_name=_('valid until'), blank=True, null=True)
    is_finalized = models.BooleanField(verbose_name=_("finalized"), default=False, editable=False)

    # text parts
    title = models.TextField(verbose_name=_('Title of catalog'))
    title_sub = models.TextField(verbose_name=_('Sub-title of catalog'), null=True, blank=True)

    copyright_note = models.TextField(verbose_name=_('copyright note'), max_length=10000,
                                      blank=True, help_text=_('LaTeX syntax allowed'))
    preface = models.TextField(verbose_name=_('preface'), max_length=10000, blank=True,
                               help_text=_('LaTeX syntax allowed'))
    notes = models.TextField(verbose_name=_('notes'), max_length=10000, blank=True,
                             help_text=_('LaTeX syntax allowed'))

    # connections to seeds/individuals
    seed = models.ManyToManyField('individuals.Individual', verbose_name=_('seed'), blank=True)

    debug_output = models.TextField(verbose_name=_("debug output"), editable=False, blank=True, default="")

    def __str__(self):
        return '%s %d %s' % (_('seed catalog'), self.pk, self.release_date)
    __str__.admin_order_field = 'release_date'

    def manage_seed_decorator(self):
        if self.is_finalized:
            return _("finalized")
        url = reverse("seedcatalog:edit_seeds", args=(self.pk,))
        return mark_safe('<a href="%s">%s</a>' % (url, _('Edit %d seeds in catalog') % self.seed.count()))
    manage_seed_decorator.short_description = _('Edit seeds in catalog')
    manage_seed_decorator.exclude_csv = True

    def pdf_file_decorator(self):
        fileTarget = '%s/pdf/catalog/catalog-%d.pdf' % (settings.MEDIA_ROOT, self.pk)
        urlTarget = '%s/pdf/catalog/catalog-%d.pdf' % (settings.MEDIA_URL, self.pk)
        if os.path.isfile(fileTarget):
            html = '<a href="%s?%s">PDF (%s)</a>' % (
                urlTarget,
                escape(datetime.datetime.now().isoformat()),
                "%s" % time.ctime(os.path.getctime(fileTarget)),
            )
        else:
            html = _("not yet created")
        if self.debug_output:
            url = reverse("seedcatalog:debug", args=(self.pk,))
            # Translators: show seed catalog debug output link hover text
            html += ' (<a href="%s" title="%s">***</a>)' % (url, _("show debug output"))
        return mark_safe(html)
    pdf_file_decorator.short_description = 'PDF'
    pdf_file_decorator.exclude_csv = True

    def generate_catalog_decorator(self):
        url = reverse("seedcatalog:generate", args=(self.pk, ))
        return mark_safe('<a href="%s">%s</a>' % (url, _("generate catalog")))
    generate_catalog_decorator.short_description = _('create')
    generate_catalog_decorator.exclude_csv = True

    def create_duplicate(self):
        """Create a clone of the current catalog
        Returns the new instance"""
        today = datetime.date.today()
        cat = SeedCatalog.objects.create(
            release_date=today,
            valid_until_date=today,
            is_finalized=False,
            title=self.title,
            title_sub=self.title_sub,
            copyright_note=self.copyright_note,
            preface=self.preface,
            notes=self.notes,
        )
        for seed in self.seed.all():
            cat.seed.add(seed)
        cat.save()
        return cat