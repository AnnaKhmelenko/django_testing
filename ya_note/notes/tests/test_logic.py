from http import HTTPStatus

from django.urls import reverse
from pytils.translit import slugify as pytils_slugify
from pytest_django.asserts import assertFormError

from notes.models import Note
from .base_test import TestBase


class TestNoteLogic(TestBase):
    """Тесты логики работы заметок."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.note_data = {
            'title': 'Тестовая заметка',
            'text': 'Текст заметки',
            'slug': 'test-note'
        }
        cls.note = Note.objects.create(author=cls.author, **cls.note_data)
        cls.new_note_data = {
            'title': 'Новая заметка',
            'text': 'Текст новой заметки',
            'slug': 'new-note'
        }

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
        Note.objects.all().delete()
        url = reverse('notes:add')
        response = self.author_client.post(url, data=self.new_note_data)
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.get()
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(note.title, self.new_note_data['title'])
        self.assertEqual(note.text, self.new_note_data['text'])
        self.assertEqual(note.slug, self.new_note_data['slug'])
        self.assertEqual(note.author, self.author)

    def test_cant_create_duplicate_slug(self):
        """Нельзя создать две заметки с одинаковым slug."""
        initial_count = Note.objects.count()
        url = reverse('notes:add')
        response = self.author_client.post(url, data=self.note_data)
        self.assertEqual(Note.objects.count(), initial_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        assertFormError(
            response.context['form'],
            'slug',
            f"{self.note_data['slug']} - такой slug уже существует, "
            "придумайте уникальное значение!"
        )

    def test_auto_slug_generation(self):
        """Slug генерируется автоматически, если не заполнен."""
        Note.objects.all().delete()
        test_data = self.note_data.copy()
        test_data.pop('slug', None)
        url = reverse('notes:add')
        response = self.author_client.post(url, data=test_data)
        self.assertRedirects(response, reverse('notes:success'))
        note = Note.objects.get()
        self.assertEqual(note.title, test_data['title'])
        self.assertEqual(note.text, test_data['text'])
        self.assertEqual(note.author, self.author)
        expected_slug = pytils_slugify(test_data['title'])
        self.assertTrue(note.slug, "Slug не был сгенерирован, поле пустое")
        self.assertEqual(note.slug, expected_slug)

    def test_author_can_edit_note(self):
        """Автор может редактировать свои заметки."""
        edit_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': self.note.slug
        }
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.author_client.post(url, data=edit_data)
        updated_note = Note.objects.get(pk=self.note.pk)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(updated_note.title, edit_data['title'])
        self.assertEqual(updated_note.text, edit_data['text'])
        self.assertEqual(updated_note.slug, edit_data['slug'])
        self.assertEqual(updated_note.author, self.author)

    def test_author_can_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.author_client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertFalse(Note.objects.filter(slug=self.note.slug).exists())

    def test_reader_cannot_edit_foreign_note(self):
        """Пользователь не может редактировать чужие заметки."""
        old_note = self.note
        edit_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': self.note.slug
        }
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.reader_client.post(url, data=edit_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        new_note = Note.objects.get(pk=old_note.pk)
        self.assertEqual(new_note.title, old_note.title)
        self.assertEqual(new_note.text, old_note.text)
        self.assertEqual(new_note.slug, old_note.slug)
        self.assertEqual(new_note.author, old_note.author)

    def test_reader_cannot_delete_foreign_note(self):
        """Пользователь не может удалять чужие заметки."""
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.reader_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTrue(Note.objects.filter(slug=self.note.slug).exists())
