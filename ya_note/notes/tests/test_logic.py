from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from pytils.translit import slugify as pytils_slugify

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

        # Клиенты для тестирования
        cls.author_client = cls.client_class()
        cls.author_client.force_login(cls.author)

        cls.reader_client = cls.client_class()
        cls.reader_client.force_login(cls.reader)

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        notes_count_before = Note.objects.count()
        url = reverse('notes:add')
        response = self.client.post(url, data=self.note_data)
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before)
        self.assertRedirects(response, f'/auth/login/?next={url}')

    def test_auth_user_can_create_note(self):
        """Авторизованный пользователь может создать заметку."""
        Note.objects.all().delete()  # Очистка БД заметок перед тестом
        new_note_data = {
            'title': 'Новая заметка',
            'text': 'Текст новой заметки',
            'slug': 'new-note'
        }
        url = reverse('notes:add')
        response = self.author_client.post(url, data=new_note_data)
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.get()
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(note.title, new_note_data['title'])
        self.assertEqual(note.text, new_note_data['text'])
        self.assertEqual(note.slug, new_note_data['slug'])
        self.assertEqual(note.author, self.author)

    def test_cant_create_duplicate_slug(self):
        """Нельзя создать две заметки с одинаковым slug."""
        initial_count = Note.objects.count()
        url = reverse('notes:add')
        response = self.author_client.post(url, data=self.note_data)
        self.assertEqual(Note.objects.count(), initial_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Получаем форму из контекста
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('slug', form.errors)
        self.assertEqual(
            form.errors['slug'],
            ['test-note - такой slug уже существует, '
             'придумайте уникальное значение!']
        )

    def test_auto_slug_generation(self):
        """Slug генерируется автоматически, если не заполнен."""
        # Очищаем БД от всех заметок перед тестом
        Note.objects.all().delete()
        test_data = self.note_data.copy()
        test_data.pop('slug', None)
        url = reverse('notes:add')
        response = self.author_client.post(url, data=test_data)
        self.assertRedirects(response, reverse('notes:success'))
        note = Note.objects.get()

        # Проверяем поля
        self.assertEqual(
            note.title, test_data['title'], "Заголовок заметки не совпадает"
        )
        self.assertEqual(
            note.text, test_data['text'], "Текст заметки не совпадает"
        )
        self.assertEqual(
            note.author, self.author, "Автор заметки не совпадает"
        )

        expected_slug = pytils_slugify(test_data['title'])
        self.assertTrue(note.slug, "Slug не был сгенерирован, поле пустое")
        self.assertEqual(
            note.slug,
            expected_slug,
            "Slug заметки не совпадает: ожидается '{}', получено '{}'".format(
                expected_slug,
                note.slug
            )
        )

    def test_author_can_edit_note(self):
        """Автор может редактировать свои заметки."""
        edit_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': self.note.slug
        }
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.author_client.post(url, data=edit_data)
        self.note.refresh_from_db()
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(self.note.title, edit_data['title'])
        self.assertEqual(self.note.text, edit_data['text'])
        self.assertEqual(self.note.slug, edit_data['slug'])

    def test_author_can_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.author_client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertFalse(Note.objects.filter(slug=self.note.slug).exists())

    def test_reader_cannot_edit_foreign_note(self):
        """Пользователь не может редактировать чужие заметки."""
        edit_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': self.note.slug
        }
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.reader_client.post(url, data=edit_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.note_data['title'])

    def test_reader_cannot_delete_foreign_note(self):
        """Пользователь не может удалять чужие заметки."""
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.reader_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTrue(Note.objects.filter(slug=self.note.slug).exists())
