import datetime

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Complete Data-Migration'

    def handle(self, *args, **options):
        from tools.data_migration import calc_all

        starttime = datetime.datetime.now()
        calc_all()
        endtime = datetime.datetime.now()

        print("TOOK %s" % (endtime - starttime))

