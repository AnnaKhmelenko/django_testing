# Стандартная библиотека
from datetime import timedelta

# Сторонние библиотеки
import pytest
from django.conf import settings
from django.test import Client
from django.utils import timezone
from django.urls import reverse

# Локальные импорты
from news.models import News, Comment


# Фикстуры для новостей
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
    News.objects.bulk_create(all_news)


@pytest.fixture
def news_obj():
    return News.objects.create(title='Тестовая новость', text='Просто текст.')


# Фикстуры для пользователей
@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Лев Толстой')


@pytest.fixture
def reader(django_user_model):
    return django_user_model.objects.create(username='Читатель простой')


# Фикстуры для клиентов
@pytest.fixture
def author_client(author):
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def reader_client(reader):
    client = Client()
    client.force_login(reader)
    return client


# Фикстуры для комментариев
@pytest.fixture
def comments(news_obj, author):
    now = timezone.now()
    for index in range(10):
        comment = Comment.objects.create(
            news=news_obj,
            author=author,
            text=f'Текст {index}',
        )
        comment.created = now + timedelta(days=index)
        comment.save()


@pytest.fixture
def comment(news_obj, author):
    return Comment.objects.create(
        news=news_obj,
        author=author,
        text='Текст комментария'
    )


# Фикстуры для тестовых данных
@pytest.fixture
def comment_data():
    return {'text': 'Текст комментария'}


@pytest.fixture
def bad_comment_data():
    from news.forms import BAD_WORDS
    return {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}


# Фикстуры для URL
@pytest.fixture
def home_url():
    return reverse('news:home')


@pytest.fixture
def detail_url(news_obj):
    return reverse('news:detail', args=(news_obj.id,))


@pytest.fixture
def login_url():
    return reverse('users:login')


@pytest.fixture
def signup_url():
    return reverse('users:signup')


@pytest.fixture
def logout_url():
    return reverse('users:logout')


@pytest.fixture
def edit_url(comment):
    return reverse('news:edit', args=(comment.id,))


@pytest.fixture
def delete_url(comment):
    return reverse('news:delete', args=(comment.id,))
