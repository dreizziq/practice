from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db import transaction
import os
from api.models import Note


class Command(BaseCommand):
    help = 'Create one demonstration note without duplicating it on restart.'

    def handle(self, *args, **options):
        password = os.environ.get('DEMO_PASSWORD')
        if not password and settings.DEBUG:
            password = 'PracticeDemo2026!'
        if not password:
            raise CommandError('Set DEMO_PASSWORD before creating demonstration accounts.')
        with transaction.atomic():
            auditors, _ = Group.objects.get_or_create(name='Auditors')
            for username in ('student1', 'student2', 'auditor'):
                user, created = User.objects.get_or_create(username=username)
                if created:
                    user.set_password(password)
                    user.save()
                    if username == 'auditor':
                        user.groups.add(auditors)
                if username != 'auditor':
                    Note.objects.get_or_create(owner=user, title=f'Заметка {username}', defaults={'body': 'Эту запись видит её владелец и аудитор.'})
        self.stdout.write(self.style.SUCCESS('Demo accounts and notes are ready. Existing passwords were preserved.'))
