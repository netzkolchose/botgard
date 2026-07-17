import json


_defaults = {}


def register_key(
        key: str,
        default,
        description=None,
        validator=None,
        translateable: bool = True,
):
    """
    Registers a key/value pair for configuration.
    :param key: string - unique identifier
    :param default: text or object - either a text or gettext-getter or an object which is json-serializeable
    :param description: str or None
    :param validator: callable(value) that raises django's ValidationError
    :param translateable: bool, for text types, if True text is translateable
    """
    is_json_candidate = isinstance(default, (list, tuple, dict))
    if is_json_candidate:
        json.dumps(default)

    # generally not good to call validators through app initialization
    #try:
    #    if validator is not None:
    #        validator(default)
    #except ImportError:  # running the validator during registering might fail because of circular imports
    #    pass

    _defaults[key] = (default, description, validator, translateable)


def get_value(key):
    from .models import KeyValue
    try:
        val = KeyValue.objects.get(key=key)
        if val.type == 't':
            return val.value
        elif val.type == 'g':
            return val.value_geo
        elif val.type == 'n':
            return val.value_normal_text
        elif val.type == 'j':
            if isinstance(val.value_json, str):
                return json.loads(val.value_json)
            return val.value_json
        else:
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
