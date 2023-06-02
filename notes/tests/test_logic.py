from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from http import HTTPStatus

from notes.forms import WARNING
from notes.models import Note

from pytils.translit import slugify


User = get_user_model()


class TestNoteCreate(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Залогиненный пользователь')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.form_data = {
            'title': 'Test Note',
            'text': 'This is a test note',
            'slug': 'test-note',
        }

    def test_user_can_create_note(self):
        url = reverse('notes:add')
        response = self.author_client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        url = reverse('notes:add')
        response = self.client.post(url, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 0)

    def test_empty_slug(self):
        self.form_data.pop('slug')
        url = reverse('notes:add')
        response = self.author_client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteAddDelete(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Залогиненный пользователь')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.form_data = {
            'title': 'Test Note',
            'text': 'This is a test note',
            'slug': 'test-note',
        }
        cls.note = Note.objects.create(
            title='Existing Note',
            text='This is an existing note',
            slug='test-note',
            author=cls.author,
        )
        cls.new_form_data = {
            'title': 'New Title',
            'text': 'Updated text',
            'slug': 'new-slug',
        }

    def test_not_unique_slug(self):
        self.form_data['slug'] = self.note.slug
        url = reverse('notes:add')
        response = self.author_client.post(url, data=self.form_data)
        self.assertFormError(
            response, 'form', 'slug', errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_author_can_edit_note(self):
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.author_client.post(url, data=self.new_form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.new_form_data['title'])
        self.assertEqual(self.note.text, self.new_form_data['text'])
        self.assertEqual(self.note.slug, self.new_form_data['slug'])

    def test_other_user_cant_edit_note(self):
        admin_client = Client()
        admin_client.force_login(User.objects.create(username='admin'))
        url = reverse('notes:edit', args=(self.note.slug,))
        response = admin_client.post(url, data=self.new_form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def test_author_can_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.author_client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        admin_client = Client()
        admin_client.force_login(User.objects.create(username='admin'))
        url = reverse('notes:delete', args=(self.note.slug,))
        response = admin_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
