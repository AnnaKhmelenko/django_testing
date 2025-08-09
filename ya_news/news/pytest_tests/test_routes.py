from http import HTTPStatus

import pytest
from pytest_lazyfixture import lazy_fixture

# Доступ к БД для всех тестов модуля
pytestmark = pytest.mark.django_db


# Константы URL-фикстур
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


def test_author_can_access_edit_and_delete(
        author_client, edit_url, delete_url
):
    for url in [edit_url, delete_url]:
        response = author_client.get(url)
        assert response.status_code == HTTPStatus.OK


def test_anonymous_redirected_to_login(
        client, edit_url, delete_url, login_url
):
    for url in [edit_url, delete_url]:
        response = client.get(url, follow=False)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url.startswith(login_url)
        assert f'next={url}' in response.url


def test_reader_cannot_edit_or_delete_foreign_comment(reader_client, comment):
    for url in [URL_EDIT, URL_DELETE]:
        response = reader_client.get(url)
        assert response.status_code == HTTPStatus.NOT_FOUND
