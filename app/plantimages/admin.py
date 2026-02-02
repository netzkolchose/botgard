import traceback

from .models import PlantImage
from tools import readOnlyAdmin
from django.contrib.admin import StackedInline
from django import forms
from django.contrib.admin import widgets
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
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
            except Exception as e:
                print(f"Exception in thumbnailer for {value}: {type(e).__name__}: {e}")
                traceback.print_exc(10)
                markup = format_html(
                    """<div><p class="error">{}<br/>{}</p></div>{}""",
                    _("Error"),
                    f"{type(e).__name__}: {e}",
                    markup,
                )
                thumb_url = None

            if thumb_url:
                markup = '<div class="image-preview-widget-wrapper"><a href="%s" target="_blank"><img width="%i" height="%i" class="preview-image" src="%s"></a>%s</div>'%(
                    url,
                    settings.THUMBNAIL_ALIASES['']['large_preview']['size'][0],
                    settings.THUMBNAIL_ALIASES['']['large_preview']['size'][1],
                    thumb_url, markup
                )

        return mark_safe(markup)


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
