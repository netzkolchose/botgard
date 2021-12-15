from django.utils.translation import gettext_lazy as _

ACCESSION_EXTENSION_CHOICES = (
    ('00', _('00 (Altbestand)')),
    ('10', _('10 (Wildsamen mit Sammeldaten)')),
    ('20', _('20 (Wildpflanze mit Sammeldaten)')),
    ('40', _('40 (Kulturpflanze/Samen mit Sammeldaten)')),
    ('50', _('50 (Wildsamen/Wildpflanzen ohne Sammeldaten)')),
    ('70', _('70 (Kultursamen)')),
    ('80', _('80 (Kulturpflanze)')),
    ('90', _('90 (Kulturpflanze/Samen wechselnder Herkünfte)')),
    ('W', _('W (Wildsamen)')),
)
