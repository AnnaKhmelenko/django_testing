import pytest
from datetime import timedelta
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from news.models import News, Comment
from news.forms import CommentForm


@pytest.fixture
def news_list():
    today = timezone.now()
    all_news = [
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index)
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    return News.objects.bulk_create(all_news)


@pytest.fixture
def news_obj():
    return News.objects.create(title='Тестовая новость', text='Просто текст.')


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Комментатор')


@pytest.fixture
def comments(news_obj, author):
    now = timezone.now()
    objs = []
    for index in range(10):
        comment = Comment.objects.create(
            news=news_obj,
            author=author,
            text=f'Текст {index}',
        )
        comment.created = now + timedelta(days=index)
        comment.save()
        objs.append(comment)
    return objs


@pytest.mark.django_db
def test_news_count_on_homepage(client, news_list):
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    assert object_list.count() == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order_on_homepage(client, news_list):
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_comments_order_on_detail_page(client, news_obj, author, comments):
    url = reverse('news:detail', args=(news_obj.id,))
    response = client.get(url)
    assert 'news' in response.context
    news_from_context = response.context['news']
    all_comments = news_from_context.comment_set.all()
    all_timestamps = [comment.created for comment in all_comments]
    sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == sorted_timestamps


@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, news_obj, comments):
    url = reverse('news:detail', args=(news_obj.id,))
    response = client.get(url)
    assert 'form' not in response.context


@pytest.mark.django_db
def test_authorized_client_has_form(client, news_obj, author, comments):
    client.force_login(author)
    url = reverse('news:detail', args=(news_obj.id,))
    response = client.get(url)
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
