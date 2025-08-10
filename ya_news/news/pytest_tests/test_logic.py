from http import HTTPStatus

import pytest
from pytest_django.asserts import assertFormError

from news.forms import WARNING
from news.models import Comment

pytestmark = pytest.mark.django_db


def test_anonymous_cannot_create_comment(client, comment_data, detail_url):
    client.post(detail_url, data=comment_data)
    assert Comment.objects.count() == 0


def test_authorized_user_can_create_comment(
    author_client, author, news_obj, comment_data, detail_url
):
    response = author_client.post(detail_url, data=comment_data)
    assert response.url.endswith('#comments')
    assert Comment.objects.count() == 1
    comment = Comment.objects.get()
    assert comment.text == comment_data['text']
    assert comment.news == news_obj
    assert comment.author == author


def test_comment_with_bad_words_not_created(
    author_client, bad_comment_data, detail_url
):
    response = author_client.post(
        detail_url, data=bad_comment_data, follow=True)
    assertFormError(response.context['form'], 'text', WARNING)
    assert Comment.objects.count() == 0


def test_author_can_delete_comment(
        author_client, comment, news_obj, detail_url, delete_url):
    url_to_comments = detail_url + '#comments'
    response = author_client.delete(delete_url)
    assert response.url == url_to_comments
    assert Comment.objects.count() == 0


def test_user_cannot_delete_foreign_comment(
        reader_client, comment, delete_url):
    response = reader_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == 1


def test_author_can_edit_comment(
    author_client, comment, comment_data, detail_url, edit_url
):
    url_to_comments = detail_url + '#comments'
    old_comment = comment
    response = author_client.post(edit_url, data=comment_data)
    assert response.url == url_to_comments

    new_comment = Comment.objects.get(pk=old_comment.id)
    assert new_comment.text == comment_data['text']
    # Поля, которые не должны измениться
    assert new_comment.news == old_comment.news
    assert new_comment.author == old_comment.author


def test_user_cannot_edit_foreign_comment(
    reader_client, comment, comment_data, edit_url
):
    old_comment = comment
    response = reader_client.post(edit_url, data=comment_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    new_comment = Comment.objects.get(pk=old_comment.id)
    assert new_comment.text == old_comment.text
    assert new_comment.news == old_comment.news
    assert new_comment.author == old_comment.author
