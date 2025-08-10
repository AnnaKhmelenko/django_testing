from django.test import TestCase
from django.contrib.auth import get_user_model

from notes.models import Note

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
