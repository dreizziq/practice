from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from api.db_backup import backup


class Command(BaseCommand):
    help = 'Create a consistent SQLite backup with a SHA-256 manifest.'

    def add_arguments(self, parser):
        parser.add_argument('--output', required=True)

    def handle(self, *args, **options):
        database = settings.DATABASES['default']
        if database['ENGINE'] != 'django.db.backends.sqlite3':
            raise CommandError('This command supports SQLite. For PostgreSQL use pg_dump; see docs/DATABASE.md.')
        try:
            path = backup(Path(database['NAME']), options['output'])
        except (OSError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f'Backup verified: {path}'))
