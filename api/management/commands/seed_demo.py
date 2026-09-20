from django.core.management.base import BaseCommand
from api.models import Note


class Command(BaseCommand):
    help = 'Create one demonstration note without duplicating it on restart.'

    def handle(self, *args, **options):
        _, created = Note.objects.get_or_create(
            title='First Note', body='This is certainly noteworthy'
        )
        self.stdout.write(self.style.SUCCESS(
            'Demo note created.' if created else 'Demo note already exists.'
        ))
