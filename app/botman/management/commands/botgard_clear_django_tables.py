import datetime

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'DANGEROUS! Clear all django-tables after initial migrations to make loaddata work'

    def handle(self, *args, **options):
        starttime = datetime.datetime.now()
        clear_django_tables()
        endtime = datetime.datetime.now()

        print("TOOK %s" % (endtime - starttime))


def clear_django_tables():
    from individuals.models import Department, Territory
    Department.objects.all().delete()
    Territory.objects.all().delete()

    from django.contrib.auth.models import Permission
    Permission.objects.all().delete()

    from django.contrib.contenttypes.models import ContentType
    ContentType.objects.all().delete()

