import json
from django.test import TestCase
from .models import Note


class NoteAPITests(TestCase):
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
        Note.objects.create(title='Keep', body='Keep this note')
        self.assertEqual(self.client.delete('/api/note/').status_code, 405)
        self.assertEqual(Note.objects.count(), 1)

    def test_invalid_update_keeps_existing_data(self):
        note = Note.objects.create(title='Original', body='Keep')
        response = self.client.put(f'/api/note/{note.pk}/',
                                  data=json.dumps({'title': '', 'body': 'Changed'}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)
        note.refresh_from_db()
        self.assertEqual((note.title, note.body), ('Original', 'Keep'))

    def test_list_pagination(self):
        Note.objects.bulk_create([Note(title=str(i), body='Text') for i in range(3)])
        data = self.client.get('/api/note/?limit=2').json()
        self.assertEqual(len(data['objects']), 2)
        self.assertEqual(data['meta']['total_count'], 3)
        self.assertIsNotNone(data['meta']['next'])
