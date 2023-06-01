from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from http import HTTPStatus

from notes.forms import WARNING
from notes.models import Note

from pytils.translit import slugify


User = get_user_model()


class NoteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Залогиненный пользователь')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

    def test_user_can_create_note(self):
        form_data = {
            'title': 'Test Note',
            'text': 'This is a test note',
            'slug': 'test-note',
        }
        url = reverse('notes:add')
        response = self.author_client.post(url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        self.assertEqual(new_note.title, form_data['title'])
        self.assertEqual(new_note.text, form_data['text'])
        self.assertEqual(new_note.slug, form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_not_unique_slug(self):
        form_data = {
            'title': 'Test Note',
            'text': 'This is a test note',
            'slug': 'test-note',
        }
        note = Note.objects.create(
            title='Existing Note',
            text='This is an existing note',
            slug='test-note',
            author=self.author,
        )
        form_data['slug'] = note.slug
        url = reverse('notes:add')
        response = self.author_client.post(url, data=form_data)

        self.assertFormError(
            response, 'form', 'slug', errors=(note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        form_data = {
            'title': 'Test Note',
            'text': 'This is a test note',
            'slug': 'test-note',
        }
        form_data.pop('slug')
        url = reverse('notes:add')
        response = self.author_client.post(url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        form_data = {
            'title': 'New Title',
            'text': 'Updated text',
            'slug': 'new-slug',
        }
        note = Note.objects.create(
            title='Existing Note',
            text='This is an existing note',
            slug='test-note',
            author=self.author,
        )
        url = reverse('notes:edit', args=(note.slug,))
        response = self.author_client.post(url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))
        note.refresh_from_db()
        self.assertEqual(note.title, form_data['title'])
        self.assertEqual(note.text, form_data['text'])
        self.assertEqual(note.slug, form_data['slug'])

    def test_other_user_cant_edit_note(self):
        admin_client = Client()
        admin_client.force_login(User.objects.create(username='admin'))
        form_data = {
            'title': 'Updated Title',
            'text': 'Updated text',
            'slug': 'updated-slug',
        }
        note = Note.objects.create(
            title='Existing Note',
            text='This is an existing note',
            slug='test-note',
            author=self.author,
        )
        url = reverse('notes:edit', args=(note.slug,))
        response = admin_client.post(url, data=form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=note.id)
        self.assertEqual(note.title, note_from_db.title)
        self.assertEqual(note.text, note_from_db.text)
        self.assertEqual(note.slug, note_from_db.slug)

    def test_author_can_delete_note(self):
        note = Note.objects.create(
            title='Existing Note',
            text='This is an existing note',
            slug='test-note',
            author=self.author,
        )
        url = reverse('notes:delete', args=(note.slug,))
        response = self.author_client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        note = Note.objects.create(
            title='Existing Note',
            text='This is an existing note',
            slug='test-note',
            author=self.author,
        )
        admin_client = Client()
        admin_client.force_login(User.objects.create(username='admin'))
        url = reverse('notes:delete', args=(note.slug,))
        response = admin_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
