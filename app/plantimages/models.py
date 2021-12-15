from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ugettext  as __


class PlantImage(models.Model):
    class Meta:
        verbose_name = _('image')
        verbose_name_plural = _('images')
    individual = models.ForeignKey('individuals.Individual', on_delete=models.CASCADE)
    image = models.ImageField(verbose_name=_('image'), upload_to='pictures/PlantImages', blank=True)
    comment = models.CharField(verbose_name=_('comment'), max_length=200, blank=True)

    def __str__(self):
        if self.image:
            return self.image.name.split('/')[-1]
        return __('no image')
