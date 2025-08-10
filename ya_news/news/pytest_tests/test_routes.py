from http import HTTPStatus

import pytest
from pytest_lazyfixture import lazy_fixture
from django.test import TestCase

pytestmark = pytest.mark.django_db

URL_HOME = lazy_fixture('home_url')
URL_DETAIL = lazy_fixture('detail_url')
URL_LOGIN = lazy_fixture('login_url')
URL_SIGNUP = lazy_fixture('signup_url')
URL_LOGOUT = lazy_fixture('logout_url')
URL_EDIT = lazy_fixture('edit_url')
URL_DELETE = lazy_fixture('delete_url')


@pytest.mark.parametrize(
    'url, expected_status',
    [
        (URL_HOME, HTTPStatus.OK),
        (URL_DETAIL, HTTPStatus.OK),
        (URL_LOGIN, HTTPStatus.OK),
        (URL_SIGNUP, HTTPStatus.OK),
        (URL_LOGOUT, HTTPStatus.METHOD_NOT_ALLOWED),
    ],
)
def test_pages_availability_for_anonymous(client, url, expected_status):
    response = client.get(url)
    assert response.status_code == expected_status


@pytest.mark.parametrize('url', [lazy_fixture('edit_url'),
                                 lazy_fixture('delete_url')])
def test_author_can_access_edit_and_delete(author_client, url):
    response = author_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize('url', [lazy_fixture('edit_url'),
                                 lazy_fixture('delete_url')])
def test_anonymous_redirected_to_login(client, url, login_url):
    response = client.get(url, follow=True)
    # Создаем экземпляр TestCase, чтобы вызвать assertRedirects
    TestCase().assertRedirects(response, f"{login_url}?next={url}")


@pytest.mark.parametrize('url', [lazy_fixture('edit_url'),
                                 lazy_fixture('delete_url')])
def test_reader_cannot_edit_or_delete_foreign_comment(reader_client, url):
    response = reader_client.get(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
