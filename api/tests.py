import json
from contextlib import closing
from django.test import TestCase
from django.contrib.auth.models import User, Group
from .models import Note


class NoteAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('owner', password='Test-password-42')
        self.client.force_login(self.user)

    def test_crud_lifecycle(self):
        response = self.client.post('/api/note/', data=json.dumps({
            'title': 'Первая заметка', 'body': 'Текст заметки',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        note = Note.objects.get()
        self.assertIsNotNone(note.created_at)
        url = f'/api/note/{note.pk}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], 'Первая заметка')
        self.assertNotIn('created_at', response.json())
        self.assertEqual(self.client.get('/api/note/').json()['meta']['total_count'], 1)
        response = self.client.put(url, data=json.dumps({
            'title': 'Обновлено', 'body': 'Новый текст',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 204)
        note.refresh_from_db()
        self.assertEqual(note.body, 'Новый текст')
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertFalse(Note.objects.exists())
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_invalid_notes_are_rejected(self):
        for data in ({'body': 'Missing title'}, {'title': 'x' * 201, 'body': 'Text'},
                     {'title': 'Title', 'body': ''}):
            with self.subTest(data=data):
                response = self.client.post('/api/note/', data=json.dumps(data),
                                            content_type='application/json')
                self.assertEqual(response.status_code, 400)
        self.assertFalse(Note.objects.exists())

    def test_malformed_json(self):
        response = self.client.post('/api/note/', data='{broken',
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_home_shows_notes_interface(self):
        response = self.client.get('/')
        self.assertContains(response, 'Notable')
        self.assertContains(response, 'id="note-form"')

    def test_admin_is_disabled_by_default(self):
        self.assertEqual(self.client.get('/admin/').status_code, 404)

    def test_bulk_delete_is_disabled(self):
        Note.objects.create(owner=self.user, title='Keep', body='Keep this note')
        self.assertEqual(self.client.delete('/api/note/').status_code, 405)
        self.assertEqual(Note.objects.count(), 1)

    def test_invalid_update_keeps_existing_data(self):
        note = Note.objects.create(owner=self.user, title='Original', body='Keep')
        response = self.client.put(f'/api/note/{note.pk}/',
                                  data=json.dumps({'title': '', 'body': 'Changed'}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)
        note.refresh_from_db()
        self.assertEqual((note.title, note.body), ('Original', 'Keep'))

    def test_list_pagination(self):
        Note.objects.bulk_create([Note(owner=self.user, title=str(i), body='Text') for i in range(3)])
        data = self.client.get('/api/note/?limit=2').json()
        self.assertEqual(len(data['objects']), 2)
        self.assertEqual(data['meta']['total_count'], 3)
        self.assertIsNotNone(data['meta']['next'])

    def test_anonymous_access_denied(self):
        self.client.logout()
        self.assertEqual(self.client.get('/api/note/').status_code, 401)
        self.assertRedirects(self.client.get('/'), '/accounts/login/?next=/')

    def test_other_users_notes_cannot_be_read_or_changed(self):
        other = User.objects.create_user('other')
        note = Note.objects.create(owner=other, title='Private', body='Secret')
        url = f'/api/note/{note.pk}/'
        self.assertEqual(self.client.get('/api/note/').json()['meta']['total_count'], 0)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.put(url, data=json.dumps({'title':'Hacked','body':'Bad'}), content_type='application/json').status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)
        note.refresh_from_db()
        self.assertEqual(note.title, 'Private')

    def test_owner_cannot_be_forged(self):
        other = User.objects.create_user('other')
        self.client.post('/api/note/', data=json.dumps({'title':'Mine','body':'Text','owner':other.pk}), content_type='application/json')
        self.assertEqual(Note.objects.get().owner_id, self.user.pk)

    def test_auditor_can_read_but_not_write(self):
        group = Group.objects.create(name='Auditors')
        self.user.groups.add(group)
        other = User.objects.create_user('other')
        note = Note.objects.create(owner=other, title='Visible', body='Text')
        self.assertEqual(self.client.get('/api/note/').json()['meta']['total_count'], 1)
        for method, url in [('post','/api/note/'),('put',f'/api/note/{note.pk}/'),('delete',f'/api/note/{note.pk}/')]:
            with self.subTest(method=method):
                response = getattr(self.client, method)(url, data=json.dumps({'title':'No','body':'No'}), content_type='application/json')
                self.assertEqual(response.status_code, 401)
        note.refresh_from_db()
        self.assertEqual(Note.objects.count(), 1)
        self.assertEqual(note.title, 'Visible')

    def test_admin_can_update_any_note(self):
        self.user.is_superuser = True
        self.user.save()
        other = User.objects.create_user('other')
        note = Note.objects.create(owner=other, title='Original', body='Text')
        response = self.client.put(f'/api/note/{note.pk}/', data=json.dumps({'title':'Admin edit','body':'Text'}), content_type='application/json')
        self.assertEqual(response.status_code, 204)

    def test_csrf_required_for_session_write(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post('/api/note/', data=json.dumps({'title':'No','body':'No'}), content_type='application/json').status_code, 401)
        client.get('/')
        token = client.cookies['csrftoken'].value
        response = client.post('/api/note/', data=json.dumps({'title':'Yes','body':'Yes'}), content_type='application/json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 201)


class BackupTests(TestCase):
    def test_roundtrip_and_no_overwrite(self):
        import sqlite3
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from .db_backup import backup, restore
        with TemporaryDirectory() as folder:
            root = Path(folder)
            source, copy, restored = [root / name for name in ('source.sqlite3','backup.sqlite3','restored.sqlite3')]
            with closing(sqlite3.connect(source)) as db, db:
                db.execute('CREATE TABLE notes (id INTEGER PRIMARY KEY, body TEXT)')
                db.execute('INSERT INTO notes VALUES (1, ?)', ('Important text',))
            backup(source, copy)
            with closing(sqlite3.connect(source)) as db, db:
                db.execute('DELETE FROM notes')
            restore(copy, restored)
            with closing(sqlite3.connect(restored)) as db:
                self.assertEqual(db.execute('SELECT body FROM notes').fetchone()[0], 'Important text')
            with self.assertRaises(FileExistsError):
                restore(copy, restored)

    def test_corrupt_backup_rejected(self):
        import sqlite3
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from .db_backup import backup, restore
        with TemporaryDirectory() as folder:
            root = Path(folder)
            source, copy, restored = [root / name for name in ('source.sqlite3','backup.sqlite3','restored.sqlite3')]
            with closing(sqlite3.connect(source)) as db, db:
                db.execute('CREATE TABLE records (id INTEGER)')
            backup(source, copy)
            with copy.open('ab') as stream:
                stream.write(b'tampered')
            with self.assertRaises(ValueError):
                restore(copy, restored)
            self.assertFalse(restored.exists())
