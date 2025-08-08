from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.reader = User.objects.create(username='Другой пользователь')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author
        )

    def test_pages_availability_for_anonymous_user(self):
        """Страницы регистрации, входа доступны анонимному пользователю."""
        urls = (
            'users:login',
            'users:signup',
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout_behavior(self):
        """Проверка поведения logout."""
        # GET запрос должен возвращать 405 (Method Not Allowed)
        response = self.client.get(reverse('users:logout'))
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

        # POST запрос без аутентификации
        response = self.client.post(reverse('users:logout'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # POST запрос с аутентификацией
        self.client.force_login(self.author)
        response = self.client.post(reverse('users:logout'))
        # В Django 5.1+ POST к logout всегда возвращает 200
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_auth_user(self):
        """Страницы заметок доступны аутентифицированному пользователю."""
        urls = (
            'notes:list',
            'notes:add',
            'notes:success',
        )
        self.client.force_login(self.author)
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_note_author(self):
        """Страницы заметки доступны автору."""
        urls = (
            'notes:detail',
            'notes:edit',
            'notes:delete',
        )
        self.client.force_login(self.author)
        for name in urls:
            with self.subTest(user=self.author.username, name=name):
                url = reverse(name, args=(self.note.slug,))
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_client(self):
        """Анонимного пользователя перенаправляет на страницу логина."""
        login_url = reverse('users:login')
        urls = (
            'notes:list',
            'notes:add',
            'notes:success',
            'notes:detail',
            'notes:edit',
            'notes:delete',
        )
        for name in urls:
            with self.subTest(name=name):
                if name in ('notes:detail', 'notes:edit', 'notes:delete'):
                    url = reverse(name, args=(self.note.slug,))
                else:
                    url = reverse(name)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_availability_for_different_users(self):
        """Страницы заметки недоступны не автору."""
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        urls = (
            'notes:detail',
            'notes:edit',
            'notes:delete',
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in urls:
                with self.subTest(user=user.username, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)
