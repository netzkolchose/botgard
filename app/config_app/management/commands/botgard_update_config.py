import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db import transaction


class Command(BaseCommand):
    help = 'Create Key-Value pairs in DB for all registered defaults. Does NOT overwrite existing settings!'

    def add_arguments(self, parser):
        parser.add_argument('-f', nargs="+",
                            help=_(
"""Force update of all (or specified values) in the DB. 
 -f all: will copy all default values over the values in the database.
 -f with a list of keys will only copy the default values for the given keys."""))

    def handle(self, *args, **options):
        starttime = datetime.datetime.now()

        from config_app import _defaults
        from config_app.models import KeyValue

        force_update = set()
        if options.get("f"):
            force_update = set(options.get("f"))
            if force_update == {"all"}:
                force_update = set(_defaults.keys())
            else:
                for f in force_update:
                    if f not in _defaults:
                        print("Unknown key '%s' in -f option" % f)
                        exit(1)

        missed_updates = []

        with transaction.atomic():
            for key in _defaults:
                value, descr, validator = _defaults[key]
                is_json = isinstance(value, (list, tuple, dict))

                qset = KeyValue.objects.filter(key=key)
                if qset.exists():
                    kv = qset[0]
                    if is_json:
                        if kv.type != "j":
                            print("WARNING: '%s' has a json default-value but database has type '%s'" % (key, kv.type))
                        elif kv.value_json != value:
                            if key not in force_update:
                                print("INFO: '%s': database json value is different but will not be updated" % key)
                                missed_updates.append(key)
                    else:
                        if kv.type != "t":
                            print("WARNING: '%s' has a text default-value but database has type '%s'" % (key, kv.type))
                        if kv.value != value:
                            if key not in force_update:
                                print("INFO: '%s': database value is different but will not be updated" % key)
                                missed_updates.append(key)

                    if key in force_update:
                        print("INFO: '%s': overwriting database value from defaults" % key)
                        kv.type = "j" if is_json else "t"
                        if is_json:
                            kv.value_json = value
                        else:
                            kv.value = value
                            # get each translated language
                            for lang, lang_name in settings.LANGUAGES:
                                with translation.override(lang):
                                    setattr(kv, "value_%s" % lang, value)
                        kv.save()

                # create new
                else:

                    kwargs = dict(key=key)
                    if is_json:
                        kwargs["value_json"] = value
                        kwargs["type"] = "j"
                    else:
                        kwargs["value"] = value
                        # get each translated language
                        for lang, lang_name in settings.LANGUAGES:
                            with translation.override(lang):
                                kwargs["value_%s" % lang] = value

                    KeyValue.objects.create(**kwargs)
                    print("INFO: '%s': created database value" % key)

        if missed_updates:
            print()
            print(_("INFO: The database contains configruation values which are different to the default settings."))
            print(_("If you want to overwrite the database changes call:"))
            print("./manage.py %s -f %s" % (
                __name__.split(".")[-1],
                " ".join(sorted(missed_updates)),
            ))

        endtime = datetime.datetime.now()
        print("TOOK %s" % (endtime - starttime))

