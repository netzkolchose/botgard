import datetime

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = '(Re-)Calculate all Outplanting statistics'

    def handle(self, *args, **options):
        from tools.data_migration import calc_outplantings, calc_individuals_outplantings

        starttime = datetime.datetime.now()
        calc_outplantings()
        calc_individuals_outplantings()
        endtime = datetime.datetime.now()

        print("TOOK %s" % (endtime - starttime))

