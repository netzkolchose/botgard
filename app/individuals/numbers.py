import datetime
import random
from typing import Union, Type, List

from django.utils.translation import gettext_lazy as _
from django.db import models

import config_app


def _number_generation_validator(val):
    from django.forms import ValidationError

    if "method" not in val:
        raise ValidationError(_('Method must be defined'))
    if val['method'] not in ('random_range', 'incremental', 'incremental_tight'):
        raise ValidationError(_('Unknown method "%s". Supported values are "random_range", "incremental" or "incremental_tight".')%val['method'])
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
    _("The method used for generating new accession numbers"),
    validator=_number_generation_validator
)

config_app.register_key(
    "order_number_generation",
    {"method": "incremental_tight", "min": 1000},
    _("The method used for generating new order numbers"),
    validator=_number_generation_validator
)


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
            qset = Model.objects.all().order_by("-%s" % fieldname)
            if qset.exists():
                max_num = max(max_num, qset.values_list(fieldname, flat=True)[0] + 1)

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
            used_numbers |= set(Model.objects.all().values_list(fieldname, flat=True))
        used_numbers = sorted(filter(lambda n: n >= method["min"], used_numbers))
        if not used_numbers:
            return method["min"]

        if used_numbers[0] > method["min"]:
            return method["min"]

        # all tightly packed?
        unused_numbers = set(range(used_numbers[0], used_numbers[-1] + 1)) - set(used_numbers)
        if not unused_numbers:
            return used_numbers[-1] + 1
        else:
            return sorted(unused_numbers)[0]

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
