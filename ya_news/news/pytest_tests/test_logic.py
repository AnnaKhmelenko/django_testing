import pytest
from http import HTTPStatus
from django.urls import reverse

from news.models import News, Comment
from news.forms import BAD_WORDS, WARNING


@pytest.fixture
def news_obj():
    return News.objects.create(title='Заголовок', text='Текст')


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def reader(django_user_model):
    return django_user_model.objects.create(username='Читатель')


@pytest.fixture
def auth_client(client, author):
    client.force_login(author)
    return client


@pytest.fixture
def reader_client(client, reader):
    client.force_login(reader)
    return client


@pytest.fixture
def comment(news_obj, author):
    return Comment.objects.create(
        news=news_obj,
        author=author,
        text='Текст комментария'
    )


@pytest.mark.django_db
def test_anonymous_cannot_create_comment(client, news_obj):
    url = reverse('news:detail', args=(news_obj.id,))
    client.post(url, data={'text': 'Текст комментария'})
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_authorized_user_can_create_comment(auth_client, author, news_obj):
    url = reverse('news:detail', args=(news_obj.id,))
    response = auth_client.post(url, data={'text': 'Текст комментария'})
    assert response.status_code == HTTPStatus.FOUND
    assert response.url.endswith('#comments')
    assert Comment.objects.count() == 1
    comment = Comment.objects.get()
    assert comment.text == 'Текст комментария'
    assert comment.news == news_obj
    assert comment.author == author


@pytest.mark.django_db
def test_comment_with_bad_words_not_created(auth_client, news_obj):
    url = reverse('news:detail', args=(news_obj.id,))
    bad_text = f'Какой-то текст, {BAD_WORDS[0]}, еще текст'
    response = auth_client.post(url, data={'text': bad_text})
    form = response.context['form']
    assert form.errors['text'] == [WARNING]
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_author_can_delete_comment(auth_client, comment, news_obj):
    url_to_comments = reverse('news:detail', args=(news_obj.id,)) + '#comments'
    delete_url = reverse('news:delete', args=(comment.id,))
    response = auth_client.delete(delete_url)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == url_to_comments
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_user_cannot_delete_foreign_comment(reader_client, comment):
    delete_url = reverse('news:delete', args=(comment.id,))
    response = reader_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == 1


@pytest.mark.django_db
def test_author_can_edit_comment(auth_client, comment, news_obj):
    url_to_comments = reverse('news:detail', args=(news_obj.id,)) + '#comments'
    edit_url = reverse('news:edit', args=(comment.id,))
    new_text = 'Обновлённый комментарий'
    response = auth_client.post(edit_url, data={'text': new_text})
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == url_to_comments
    comment.refresh_from_db()
    assert comment.text == new_text


@pytest.mark.django_db
def test_user_cannot_edit_foreign_comment(reader_client, comment):
    old_text = comment.text
    edit_url = reverse('news:edit', args=(comment.id,))
    response = reader_client.post(edit_url, data={'text': 'Новое'})
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == old_text
