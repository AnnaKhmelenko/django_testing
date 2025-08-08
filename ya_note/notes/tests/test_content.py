from http import HTTPStatus
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note

User = get_user_model()


class TestNotesContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Другой пользователь')

        cls.author_note = Note.objects.create(
            title='Заголовок автора',
            text='Текст заметки автора',
            slug='author-note',
            author=cls.author
        )

        cls.reader_note = Note.objects.create(
            title='Заголовок читателя',
            text='Текст заметки читателя',
            slug='reader-note',
            author=cls.reader
        )

    def test_note_in_object_list_for_owner(self):
        """Заметка автора попадает в object_list на странице списка заметок."""
        self.client.force_login(self.author)
        url = reverse('notes:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        object_list = response.context['object_list']
        self.assertIn(self.author_note, object_list)
        self.assertNotIn(self.reader_note, object_list)

    def test_other_users_notes_not_in_list(self):
        """В список заметок пользователя не попадают"""
        """заметки других пользователей."""
        self.client.force_login(self.reader)
        url = reverse('notes:list')
        response = self.client.get(url)
        object_list = response.context['object_list']
        self.assertIn(self.reader_note, object_list)
        self.assertNotIn(self.author_note, object_list)

    def test_forms_in_create_and_edit_pages(self):
        """На страницы создания и редактирования заметки передаётся форма."""
        self.client.force_login(self.author)
        urls = [
            reverse('notes:add'),
            reverse('notes:edit', args=(self.author_note.slug,))
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertIn('form', response.context)
