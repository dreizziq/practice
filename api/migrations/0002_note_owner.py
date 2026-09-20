from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def archive_existing_notes(apps, schema_editor):
    Note = apps.get_model('api', 'Note')
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    alias = schema_editor.connection.alias
    notes = Note.objects.using(alias).filter(owner__isnull=True)
    if not notes.exists():
        return
    name = '_legacy_notes_archive'
    while User.objects.using(alias).filter(username=name).exists():
        name += '_'
    owner = User.objects.using(alias).create(username=name, password='!', is_active=False)
    notes.update(owner_id=owner.pk)


class Migration(migrations.Migration):
    dependencies = [('api', '0001_initial'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AddField(model_name='note', name='owner', field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='notes', to=settings.AUTH_USER_MODEL)),
        migrations.RunPython(archive_existing_notes, migrations.RunPython.noop),
        migrations.AlterField(model_name='note', name='owner', field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notes', to=settings.AUTH_USER_MODEL)),
        migrations.AddConstraint(model_name='note', constraint=models.CheckConstraint(condition=~models.Q(title=''), name='note_title_not_empty')),
        migrations.AddConstraint(model_name='note', constraint=models.CheckConstraint(condition=~models.Q(body=''), name='note_body_not_empty')),
    ]
