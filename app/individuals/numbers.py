import datetime
import random

from django.utils.translation import gettext_lazy as _

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


def _get_new_number(Model, fieldname, method):
    if method["method"] == "random_range":
        start_time = datetime.datetime.now()

        while True:
            # let's get a candidate for a new accession number
            candidate = random.randint(method["min"], method["max"])

            # make sure there is no individual with that accession number
            if not Model.objects.filter(**{fieldname: candidate}).exists():
                return candidate

            if (datetime.datetime.now() - start_time).total_seconds() > 5:
                return None

    # fast version - will pick the highest + 1
    elif method["method"] == "incremental":

        qset = Model.objects.all()
        if not qset.exists():
            return method["min"]

        return getattr(qset.order_by("-%s" % fieldname)[0], fieldname) + 1

    # slow version - will also pick free numbers in between
    elif method["method"] == "incremental_tight":

        qset = Model.objects.all()
        if not qset.exists():
            return method["min"]

        qset = qset.filter(**{"%s__gte" % fieldname: method["min"]})
        if not qset.exists():
            return method["min"]
        nums = sorted(qset.values_list(fieldname, flat=True))
        prev = nums[0]
        for n in nums:
            if n > prev+1:
                return prev+1
            prev = n
        return nums[-1] + 1


    raise ValueError("Unknown number generation method '%s'" % method["method"])


def get_new_accession_number():
    '''
    get an available accession_number for new individuals
    '''
    from individuals.models import Individual
    method = config_app.get_value('accession_generation')
    num = _get_new_number(Individual, "accession_number", method)
    if num is None:
        raise RuntimeError(_('Could not find a free accession_number in time, sorry'))
    return num


def get_new_order_number():
    '''
    get an available order_number for seeds of new individuals
    '''
    from individuals.models import Individual
    method = config_app.get_value('order_number_generation')
    num = _get_new_number(Individual, "order_number", method)
    if num is None:
        raise RuntimeError(_('Could not find a free order_number in time, sorry'))
    return num

