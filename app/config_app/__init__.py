import json
from django.utils.translation import gettext_lazy as _

_defaults = {}


def register_key(key, default, description=None, validator=None):
    """
    Registers a key/value pair for configuration.
    :param key: string - unique identifier
    :param default: text or object - either a text or gettext-getter or an object which is json-serializeable
    """
    is_json_candidate = isinstance(default, (list, tuple, dict))
    if is_json_candidate:
        json.dumps(default)

    if validator is not None:
        validator(default)

    _defaults[key] = (default, description, validator)


def get_value(key):
    from .models import KeyValue
    try:
        val = KeyValue.objects.get(key=key)
        if val.type == 't':
            return val.value
        if val.type == 'j':
            if isinstance(val.value_json, str):
                return json.loads(val.value_json)
            return val.value_json
        raise ValueError('Invalid type \'%s\' in KeyValue \'%s\'' % (val.type, val.key))
    except KeyValue.DoesNotExist:
        return _defaults[key][0]


def get_description(key):
    return _defaults[key][1]


def get_validator(key):
    if key in _defaults:
        return _defaults[key][2]
    else:
        return lambda value: True
