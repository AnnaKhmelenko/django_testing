import pytest
from http import HTTPStatus
from django.urls import reverse

from news.models import News, Comment


@pytest.fixture
def news():
    return News.objects.create(title='Заголовок', text='Текст')


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Лев Толстой')


@pytest.fixture
def reader(django_user_model):
    return django_user_model.objects.create(username='Читатель простой')


@pytest.fixture
def comment(news, author):
    return Comment.objects.create(
        news=news,
        author=author,
        text='Текст комментария'
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args',
    (
        ('news:home', None),
        ('news:detail', lambda news: (news.id,)),
    ),
)
def test_pages_available_for_anonymous(client, name, args, news):
    if callable(args):
        args = args(news)
    url = reverse(name, args=args)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args, expected_status',
    (
        ('users:login', None, HTTPStatus.OK),
        ('users:signup', None, HTTPStatus.OK),
        ('users:logout', None, HTTPStatus.METHOD_NOT_ALLOWED),
    ),
)
def test_user_auth_pages_are_available_for_anonymous(
    client, name, args, expected_status
):
    url = reverse(name, args=args)
    response = client.get(url)
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize('route', ('news:edit', 'news:delete'))
def test_author_can_access_edit_and_delete(client, author, comment, route):
    client.force_login(author)
    url = reverse(route, args=(comment.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize('route', ('news:edit', 'news:delete'))
def test_anonymous_redirected_to_login(client, comment, route):
    login_url = reverse('users:login')
    url = reverse(route, args=(comment.id,))
    expected_redirect = f'{login_url}?next={url}'
    response = client.get(url)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == expected_redirect


@pytest.mark.django_db
@pytest.mark.parametrize('route', ('news:edit', 'news:delete'))
def test_reader_cannot_edit_or_delete_foreign_comment(
    client, reader, comment, route
):
    client.force_login(reader)
    url = reverse(route, args=(comment.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
