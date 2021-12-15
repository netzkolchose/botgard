from .models import PlantImage
from tools import readOnlyAdmin
from django.contrib.admin import StackedInline
from django import forms
from django.contrib.admin import widgets
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.conf import settings


class ImagePreviewWidget(widgets.AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        markup = super(ImagePreviewWidget, self).render(name, value, attrs)

        if value:
            from easy_thumbnails.files import get_thumbnailer
            from easy_thumbnails.exceptions import InvalidImageFormatError

            url = "%s%s" % (settings.MEDIA_URL, value)
            try:
                thumb_url = get_thumbnailer(value)['large_preview'].url
            except (InvalidImageFormatError, ValueError, ):
                return markup

            markup = '<div class="image-preview-widget-wrapper"><a href="%s" target="_blank"><img width="%i" height="%i" class="preview-image" src="%s"></a>%s</div>'%(
                url,
                settings.THUMBNAIL_ALIASES['']['large_preview']['size'][0],
                settings.THUMBNAIL_ALIASES['']['large_preview']['size'][1],
                thumb_url, markup)

        return markup


class PlantImageInlineForm(forms.ModelForm):
    # def __init__(self, *args, **kwars):
    #     super(PlantImageInlineForm, self).__init__(*args, **kwars)
    #     print (self.fields['image'].widget)

    exclude = []

    class Meta:
        widgets = {
            'image': ImagePreviewWidget
        }


class PlantImageInline(readOnlyAdmin.ReadOnlyStackedInline):
    form = PlantImageInlineForm
    model = PlantImage
    extra = 2

    class Media:
        css = {"screen": (
                '/static/plantimages/plantimages_edit.css',
            )
        }
