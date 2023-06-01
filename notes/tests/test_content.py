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
        response_author = self.author_client.get(url)
        response_admin = self.admin_client.get(url)
        object_list_author = response_author.context['object_list']
        object_list_admin = response_admin.context['object_list']
        self.assertEqual(self.note in object_list_author, True)
        self.assertEqual(self.note in object_list_admin, False)

    def test_pages_contains_form(self):
        url_add = reverse('notes:add')
        response_add = self.author_client.get(url_add)
        self.assertIn('form', response_add.context)

        url_edit = reverse('notes:edit', args=[self.note.slug])
        response_edit = self.author_client.get(url_edit)
        self.assertIn('form', response_edit.context)
