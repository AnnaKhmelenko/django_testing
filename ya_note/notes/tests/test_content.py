from http import HTTPStatus
from django.urls import reverse

from notes.forms import NoteForm
from .base_test import TestBase


class TestNotesContent(TestBase):
    """Тесты контента страниц заметок."""

    def test_notes_in_object_list(self):
        """Проверка отображения заметок в списке."""
        # В каждом кортеже два элемента: клиент и ожидаемое значение
        # для выражения "<заметка> in object_list".
        test_cases = [
            (self.author_client, True),   # автор видит свою заметку
            (self.reader_client, False),  # читатель не видит чужую заметку
        ]

        url = reverse('notes:list')

        for client, expected in test_cases:
            with self.subTest(client=client):
                response = client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                object_list = response.context['object_list']
                self.assertIs(self.author_note in object_list, expected)

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
