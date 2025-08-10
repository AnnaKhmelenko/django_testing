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

        # Вынесем ссылки для тестов в атрибуты класса
        cls.login_url = reverse('users:login')
        cls.signup_url = reverse('users:signup')
        cls.logout_url = reverse('users:logout')

    def test_pages_availability_for_anonymous_user(self):
        """Страницы регистрации, входа доступны анонимному пользователю."""
        urls = (
            self.login_url,
            self.signup_url,
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout_behavior(self):
        """Проверка поведения logout."""
        for user in (None, self.author):
            if user:
                self.client.force_login(user)
            else:
                self.client.logout()
            with self.subTest(user=user.username if user else 'anonymous'):
                response = self.client.post(self.logout_url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_auth_user(self):
        """Страницы заметок доступны аутентифицированному пользователю."""
        urls = (
            reverse('notes:list'),
            reverse('notes:add'),
            reverse('notes:success'),
        )
        self.client.force_login(self.author)
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_note_author(self):
        """Страницы заметки доступны автору."""
        urls = (
            reverse('notes:detail', args=(self.note.slug,)),
            reverse('notes:edit', args=(self.note.slug,)),
            reverse('notes:delete', args=(self.note.slug,)),
        )
        self.client.force_login(self.author)
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_client(self):
        """Анонимного пользователя перенаправляет на страницу логина."""
        login_url = reverse('users:login')
        url_names = (
            'notes:list',
            'notes:add',
            'notes:success',
            'notes:detail',
            'notes:edit',
            'notes:delete',
        )
        for name in url_names:
            if name in ('notes:detail', 'notes:edit', 'notes:delete'):
                url = reverse(name, args=(self.note.slug,))
            else:
                url = reverse(name)
            redirect_url = f'{login_url}?next={url}'
            with self.subTest(url=url):
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
