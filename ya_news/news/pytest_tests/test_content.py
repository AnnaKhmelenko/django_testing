import pytest
from django.conf import settings
from django.urls import reverse

from news.forms import CommentForm

# Доступ к БД для всех тестов модуля
pytestmark = pytest.mark.django_db


def test_news_count_on_homepage(client, news_list):
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    assert object_list.count() == settings.NEWS_COUNT_ON_HOME_PAGE


def test_news_order_on_homepage(client, news_list):
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


def test_comments_order_on_detail_page(client, news_obj, author, comments):
    url = reverse('news:detail', args=(news_obj.id,))
    response = client.get(url)
    assert 'news' in response.context
    news_from_context = response.context['news']
    all_comments = news_from_context.comment_set.all()
    all_timestamps = [comment.created for comment in all_comments]
    sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == sorted_timestamps


def test_anonymous_client_has_no_form(client, news_obj, comments):
    url = reverse('news:detail', args=(news_obj.id,))
    response = client.get(url)
    assert 'form' not in response.context


def test_authorized_client_has_form(client, news_obj, author, comments):
    client.force_login(author)
    url = reverse('news:detail', args=(news_obj.id,))
    response = client.get(url)
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
