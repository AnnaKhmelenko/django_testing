from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note
from notes.forms import NoteForm


User = get_user_model()


class TestBase(TestCase):
    """Базовый класс для тестов с общими фикстурами."""

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

        cls.author_client = cls.client_class()
        cls.author_client.force_login(cls.author)

        cls.reader_client = cls.client_class()
        cls.reader_client.force_login(cls.reader)


class TestNotesContent(TestBase):
    """Тесты контента страниц заметок."""

    def test_notes_in_object_list(self):
        """Проверка отображения заметок в списке."""
        # Создаем заметку для читателя
        reader_note = Note.objects.create(
            title='Заголовок читателя',
            text='Текст заметки читателя',
            slug='reader-note',
            author=self.reader
        )

        test_cases = [
            (self.author_client, self.author_note, reader_note),
            (self.reader_client, reader_note, self.author_note),
        ]

        url = reverse('notes:list')

        for client, own_note, others_note in test_cases:
            with self.subTest(client=client, own_note=own_note):
                response = client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                object_list = response.context['object_list']
                self.assertIn(own_note, object_list)
                self.assertNotIn(others_note, object_list)

    def test_forms_in_create_and_edit_pages(self):
        """Проверка формы на страницах создания и редактирования."""
        urls = [
            reverse('notes:add'),
            reverse('notes:edit', args=(self.author_note.slug,))
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
