from django.core.management.base import BaseCommand, CommandError
from api.db_backup import restore


class Command(BaseCommand):
    help = 'Verify and restore a SQLite backup into a NEW file without replacing the live database.'

    def add_arguments(self, parser):
        parser.add_argument('backup')
        parser.add_argument('--output', required=True)

    def handle(self, *args, **options):
        try:
            path = restore(options['backup'], options['output'])
        except (OSError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f'Restored and verified: {path}'))
