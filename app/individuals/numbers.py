import datetime
import random
from typing import Union, Type, List

from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str
from django.db import models

import config_app


VALID_NUMBER_METHODS = (
    'random_range', 'incremental', 'incremental_tight', 'empty'
)

NUMBER_METHOD_HELP_TEXT = (
    "<br>The object must at least have the attribute 'method', e.g. <code>{\"method\": \"empty\"}</code>"
    "<br>Available methods are:\n<ul>\n"
    "<li><b>empty</b>: Do not create a number automatically</li>\n"
    "<li><b>random_range</b>: A random number between attributes 'min' and 'max'</li>\n"
    "<li><b>incremental</b>: Increasing numbers starting at 'min' (skips existing number gaps)</li>\n"
    "<li><b>incremental_tight</b>: Increasing numbers starting at 'min' (will also pick free numbers in existing gaps)</li>\n"
    "</ul>"
)

def _number_generation_validator(val):
    from django.forms import ValidationError

    if "method" not in val:
        raise ValidationError(_('Method must be defined'))
    if val['method'] not in VALID_NUMBER_METHODS:
        raise ValidationError(_('Unknown method "%s". Supported values are %s.') % (
            val['method'],
            ", ".join(f'"{m}"' for m in VALID_NUMBER_METHODS)
        ))
    if val['method'] not in ("empty",):
        if 'min' not in val:
            raise ValidationError(_('Property "min" must be specified.'))
        if not isinstance(val['min'], int):
            raise ValidationError(_('Property "min" must be of type int or long.'))
    if val['method'] in ('random_range', ):
        if 'max' not in val or 'min' not in val:
            raise ValidationError(_('Method specified requires "min" and "max" properties.'))
        if not isinstance(val['max'], int):
            raise ValidationError(_('Property "max" must be of type int or long.'))
        if (val['max'] - val['min']) < 100000:
            raise ValidationError(_('Property "max" must be much larger than "min". :)'))


config_app.register_key(
    "accession_generation",
    {"method": "random_range", "min": 7000000, "max": 7999999},
    _("The method used for generating new accession numbers") + force_str(NUMBER_METHOD_HELP_TEXT),
    validator=_number_generation_validator
)

config_app.register_key(
    "order_number_generation",
    {"method": "incremental_tight", "min": 1000},
    _("The method used for generating new order numbers") + force_str(NUMBER_METHOD_HELP_TEXT),
    validator=_number_generation_validator
)


def _lowest_gap_binary(l):
    """
    Find lowest number gap in list ``l`` with binary search.
    It is important that ``l`` comes presorted.
    """
    offset = l[0]
    mi = offset
    ma = len(l) + offset - 1
    # fast path: properly filled sequence
    if l[-1] == ma:
        return ma + 1
    while ma > mi:
        mid = (ma + mi) >> 1
        if l[mid - offset] == mid:
            mi = mid
            if l[mid - offset + 1] != mid + 1:
                return mi + 1
        else:
            ma = mid
            if l[mid - offset - 1] == ma - 1:
                return ma
    # should never be reached
    return l[-1] + 1


def _get_new_number(
        Model: Union[Type[models.Model], List[Type[models.Model]]],
        fieldname: str,
        method: dict,
):
    if isinstance(Model, list):
        model_classes = Model
    else:
        model_classes = [Model]

    if method["method"] == "random_range":
        start_time = datetime.datetime.now()

        while True:
            # let's get a candidate for a new accession number
            candidate = random.randint(method["min"], method["max"])

            # make sure there is no individual with that accession number
            is_unused = True
            for Model in model_classes:
                if Model.objects.filter(**{fieldname: candidate}).exists():
                    is_unused = False
                    break

            if is_unused:
                return candidate

            if (datetime.datetime.now() - start_time).total_seconds() > 5:
                return None

    # fast version - will pick the highest + 1
    elif method["method"] == "incremental":

        is_empty = True
        for Model in model_classes:
            qset = Model.objects.all()
            if qset.exists():
                is_empty = False
                break

        if is_empty:
            return method["min"]

        max_num = method["min"]
        for Model in model_classes:
            qset = Model.objects.filter(**{f"{fieldname}__regex": r"^\d+$"}).order_by(f"-{fieldname}")
            if qset.exists():
                max_num = max(max_num, int(qset.values_list(fieldname, flat=True)[0]) + 1)

        return max_num

    # slow version - will also pick free numbers in between
    elif method["method"] == "incremental_tight":

        is_empty = True
        for Model in model_classes:
            qset = Model.objects.all()
            if qset.exists():
                is_empty = False
                break

        if is_empty:
            return method["min"]

        used_numbers = set()
        for Model in model_classes:
            used_numbers |= set(
                map(
                    int,
                    Model.objects.filter(**{f"{fieldname}__regex": r"^\d+$"}).values_list(fieldname, flat=True),
                )
            )
        used_numbers = sorted(filter(lambda n: n >= method["min"], used_numbers))
        if not used_numbers:
            return method["min"]

        if used_numbers[0] > method["min"]:
            return method["min"]

        # used_numbers contains gaps?
        return _lowest_gap_binary(used_numbers)

    elif method["method"] == "empty":
        return ""

    raise ValueError("Unknown number generation method '%s'" % method["method"])


def get_new_accession_number():
    """
    get an available accession_number for new individuals
    """
    from individuals.models import Individual
    from entrybook.models import Entry

    method = config_app.get_value('accession_generation')
    num = _get_new_number([Individual, Entry], "accession_number", method)
    if num is None:
        raise RuntimeError(_('Could not find a free accession_number in time, sorry'))
    return num


def get_new_order_number():
    """
    get an available order_number for seeds of new individuals
    """
    from individuals.models import Individual
    from entrybook.models import Entry

    method = config_app.get_value('order_number_generation')
    num = _get_new_number([Individual, Entry], "order_number", method)
    if num is None:
        raise RuntimeError(_('Could not find a free order_number in time, sorry'))
    return num


def _validate_ipen_creation(code):
    from django.forms import ValidationError
    from individuals.models.individual import Individual
    from botman.models import BotanicGarden
    indi = Individual(
        ipen_country="XX",
        ipen_transfer_restricted="0",
        ipen_accession_number="1234",
        ipen_garden_code=BotanicGarden(code="ABC"),
        accession_extension="10",
    )
    indi.pk = 1
    try:
        generate_individual_ipen(indi, code=code)
    except Exception as e:
        raise ValidationError(f"{type(e).__name__}: {e}")


config_app.register_key(
    "ipen_creation_individual",
    default=""""{}-{}-{}-{}".format(
str.upper(self.ipen_country),
str.upper(self.ipen_transfer_restricted),
str.upper(self.ipen_garden_code.code or "XX"),
self.ipen_accession_number,
)""",
    description="A python one-liner that generates the full IPEN from an individual. The individual is available as `self`",
    validator=_validate_ipen_creation,
    translateable=False,
)


def generate_individual_ipen(individual, code=None):
    if code is None:
        code = config_app.get_value("ipen_creation_individual")
    return eval(code, {"self": individual})
