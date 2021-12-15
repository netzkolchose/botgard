from django.template import Library
from django.utils.safestring import mark_safe
from django.urls import resolve, reverse, translate_url
from django.utils.translation import activate, get_language
from django.utils.safestring import SafeString
from django.conf import settings

register = Library()

@register.filter
def all_models_hidden(app):
    """
    :param app:
    :return: True if all models shall be hidden False otherwise
    """
    return_val = True
    if "models" in app:
        for model in app["models"]:
            if "perms" in model:
                if "index_list_hide" in model["perms"]:
                    return_val = not model["perms"]["index_list_hide"]

    return return_val


@register.simple_tag(takes_context=True)
def change_lang(context, lang=None, *args, **kwargs):
    """
    Get active page's url by a specified language
    Usage: {% change_lang 'en' %}
    """
    path = context['request'].path
    return translate_url(path, lang)


@register.simple_tag(takes_context=False)
def get_license(*args, **kwargs):
    if get_license.rendered_markup:
        return get_license.rendered_markup

    data = (settings.BASE_DIR / "LICENSE.TXT").read_text()

    import mistune
    get_license.rendered_markup = SafeString(mistune.markdown(data))

    return get_license.rendered_markup
get_license.rendered_markup = None

