from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Delete all configured key-value pairs from DB!'

    def handle(self, *args, **options):
        from config_app.models import KeyValue
        KeyValue.objects.all().delete()

