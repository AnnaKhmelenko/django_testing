from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.text import slugify

from notes.models import Note

User = get_user_model()


class TestNoteLogic(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.note_data = {
            'title': 'Тестовая заметка',
            'text': 'Текст заметки',
            'slug': 'test-note'
        }
        cls.note = Note.objects.create(author=cls.author, **cls.note_data)

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        notes_count_before = Note.objects.count()
        response = self.client.post(reverse('notes:add'), data=self.note_data)
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before)
        self.assertEqual(response.status_code, 302)

    def test_auth_user_can_create_note(self):
        """Авторизованный пользователь может создать заметку."""
        self.client.force_login(self.author)
        notes_count_before = Note.objects.count()
        new_note_data = {
            'title': 'Новая заметка',
            'text': 'Текст новой заметки',
            'slug': 'new-note'
        }
        response = self.client.post(reverse('notes:add'), data=new_note_data)
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before + 1)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Note.objects.filter(slug='new-note').exists())

    def test_cant_create_duplicate_slug(self):
        """Нельзя создать две заметки с одинаковым slug."""
        self.client.force_login(self.author)
        initial_count = Note.objects.count()
        response = self.client.post(
            reverse('notes:add'),
            data=self.note_data
        )

        # Проверки
        self.assertEqual(Note.objects.count(), initial_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        form = response.context.get('form')
        self.assertIsNotNone(form, "Форма не найдена в контексте ответа")
        self.assertFalse(form.is_valid())
        self.assertIn('slug', form.errors)

        # Проверка сообщения об ошибке
        error_msg = (
            'test-note - такой slug уже существует, '
            'придумайте уникальное значение!'
        )
        self.assertEqual(form.errors['slug'], [error_msg])

    def test_auto_slug_generation(self):
        """Slug генерируется автоматически, если не заполнен."""
        self.client.force_login(self.author)
        note_data = {
            'title': 'Заметка без slug',
            'text': 'Текст заметки',
            'slug': ''  # Оставляем slug пустым
        }
        response = self.client.post(reverse('notes:add'), data=note_data)
        self.assertEqual(response.status_code, 302)

        # Проверяем, что заметка создалась с автоматическим slug
        note = Note.objects.get(title='Заметка без slug')

        # Ожидаем правильный slug для русского текста
        expected_slug = 'zametka-bez-slug'
        self.assertEqual(note.slug, expected_slug)

        # Проверяем, что slug не пустой
        self.assertTrue(len(note.slug) > 0)

        # Проверяем, что slug соответствует title
        self.assertTrue(slugify(note_data['title']) in note.slug)

    def test_author_can_edit_delete_note(self):
        """Автор может редактировать и удалять свои заметки."""
        self.client.force_login(self.author)

        # Проверка редактирования
        edit_url = reverse('notes:edit', args=(self.note.slug,))
        edit_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': self.note.slug
        }
        response = self.client.post(edit_url, data=edit_data)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, 'Новый заголовок')
        self.assertEqual(response.status_code, 302)

        # Проверка удаления
        delete_url = reverse('notes:delete', args=(self.note.slug,))
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Note.objects.filter(slug=self.note.slug).exists())
