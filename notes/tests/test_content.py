from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note


User = get_user_model()


class NoteContentTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.admin = User.objects.create(username='Админ')
        cls.admin_client = Client()
        cls.admin_client.force_login(cls.admin)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )

    def test_notes_list_for_different_users(self):
        url = reverse('notes:list')
        clients = (
            (self.author_client, True),
            (self.admin_client, False),
        )
        for client, note_in_list in clients:
            with self.subTest(client=client):
                response = client.get(url)
                object_list = response.context['object_list']
                self.assertEqual(self.note in object_list, note_in_list)

    def test_pages_contains_form(self):    
        urls = [
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        ]
        for url_name, args in urls:
            with self.subTest(url_name=url_name):
                url = reverse(url_name, args=args) if args else reverse(url_name)
                response = self.author_client.get(url)
                self.assertIn('form', response.context)
