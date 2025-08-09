from http import HTTPStatus

import pytest
from django.urls import reverse

from news.forms import WARNING
from news.models import Comment


pytestmark = pytest.mark.django_db


def test_anonymous_cannot_create_comment(client, news_obj, comment_data):
    url = reverse('news:detail', args=(news_obj.id,))
    client.post(url, data=comment_data)
    assert Comment.objects.count() == 0


def test_authorized_user_can_create_comment(
    author_client, author, news_obj, comment_data
):
    url = reverse('news:detail', args=(news_obj.id,))
    response = author_client.post(url, data=comment_data)
    assert response.url.endswith('#comments')
    assert Comment.objects.count() == 1
    comment = Comment.objects.get()
    assert comment.text == comment_data['text']
    assert comment.news == news_obj
    assert comment.author == author


def test_comment_with_bad_words_not_created(
        author_client, news_obj, bad_comment_data
):
    url = reverse('news:detail', args=(news_obj.id,))
    response = author_client.post(url, data=bad_comment_data, follow=True)
    assert 'form' in response.context
    assert WARNING in response.context['form'].errors['text']
    assert Comment.objects.count() == 0


def test_author_can_delete_comment(author_client, comment, news_obj):
    url_to_comments = reverse('news:detail', args=(news_obj.id,)) + '#comments'
    delete_url = reverse('news:delete', args=(comment.id,))
    response = author_client.delete(delete_url)
    assert response.url == url_to_comments
    assert Comment.objects.count() == 0


def test_user_cannot_delete_foreign_comment(reader_client, comment):
    delete_url = reverse('news:delete', args=(comment.id,))
    response = reader_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == 1


def test_author_can_edit_comment(
    author_client, comment, news_obj, comment_data
):
    url_to_comments = reverse('news:detail', args=(news_obj.id,)) + '#comments'
    edit_url = reverse('news:edit', args=(comment.id,))
    response = author_client.post(edit_url, data=comment_data)
    assert response.url == url_to_comments
    comment.refresh_from_db()
    assert comment.text == comment_data['text']
    assert comment.news == news_obj


def test_user_cannot_edit_foreign_comment(
    reader_client, comment, comment_data
):
    old_text = comment.text
    edit_url = reverse('news:edit', args=(comment.id,))
    response = reader_client.post(edit_url, data=comment_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == old_text
