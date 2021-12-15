from django.template import Library

import config_app

register = Library()


@register.simple_tag
def config_app_value(key):
    return config_app.get_value(key)


@register.filter
def config_app_value(key):
    return config_app.get_value(key)
