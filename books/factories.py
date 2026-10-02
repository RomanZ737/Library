from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from books.models import Author, Book, BookGenre

User = get_user_model()


def create_user(email='user@test.com', password='testpass123', **kwargs):
    return User.objects.create_user(email=email, password=password, **kwargs)


def create_admin(email='admin@test.com', password='testpass123'):
    user = User.objects.create_user(email=email, password=password, is_staff=True)
    group, _ = Group.objects.get_or_create(name='Администраторы')
    user.groups.add(group)
    return user


def create_author(**kwargs):
    defaults = {
        'first_name': 'Иван',
        'last_name': 'Иванов',
        'date_of_birth': date(1970, 1, 1),
    }
    defaults.update(kwargs)
    return Author.objects.create(**defaults)


def create_book(author=None, **kwargs):
    if author is None:
        author = create_author()
    defaults = {
        'name': 'Тестовая книга',
        'author': author,
        'release_date': date(2020, 1, 1),
        'genre': BookGenre.FICTION,
        'annotation': 'Аннотация',
    }
    defaults.update(kwargs)
    return Book.objects.create(**defaults)
