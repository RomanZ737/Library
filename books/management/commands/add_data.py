import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from books.models import Author, Book, BookGenre

User = get_user_model()
fake = Faker("ru_RU")


class Command(BaseCommand):
    help = "Заполняет базу тестовыми данными: авторы, книги, пользователи"

    AUTHORS_COUNT = 10
    BOOKS_COUNT = 20
    USERS_COUNT = 5
    USER_PASSWORD = "testpass123"

    @transaction.atomic
    def handle(self, *args, **options):
        authors, authors_created = self._ensure_authors(self.AUTHORS_COUNT)
        books, books_created = self._ensure_books(self.BOOKS_COUNT, authors)
        users, users_created = self._ensure_users(self.USERS_COUNT)

        self.stdout.write(
            self.style.SUCCESS(
                f"Авторы:     создано {authors_created:>3}, всего в БД {len(authors)}\n"
                f"Книги:      создано {books_created:>3}, всего в БД {len(books)}\n"
                f"Пользователи: создано {users_created:>3}, всего по seed-email {len(users)}\n"
                f"Пароль для новых пользователей: {self.USER_PASSWORD}"
            )
        )

    def _ensure_authors(self, target):
        existing = list(Author.objects.all())
        to_create = max(0, target - len(existing))
        created = []
        for _ in range(to_create):
            created.append(
                Author.objects.create(
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    middle_name=fake.middle_name() if random.random() > 0.5 else None,
                    date_of_birth=fake.date_of_birth(minimum_age=25, maximum_age=90),
                    comment=(
                        fake.text(max_nb_chars=200) if random.random() > 0.7 else None
                    ),
                )
            )
        return existing + created, len(created)

    def _ensure_books(self, target, authors):
        if not authors:
            self.stdout.write(self.style.WARNING("Нет авторов — книги не создаём."))
            return [], 0
        existing = list(Book.objects.all())
        to_create = max(0, target - len(existing))
        genres = [g[0] for g in BookGenre.choices]
        created = []
        for _ in range(to_create):
            created.append(
                Book.objects.create(
                    name=fake.sentence(nb_words=3).rstrip("."),
                    author=random.choice(authors),
                    release_date=fake.date_between(start_date="-30y", end_date="today"),
                    genre=random.choice(genres),
                    annotation=fake.text(max_nb_chars=500),
                )
            )
        return existing + created, len(created)

    def _ensure_users(self, target):
        users = []
        created = 0
        for i in range(1, target + 1):
            email = f"user{i}@example.com"
            user = User.objects.filter(email=email).first()
            if user is None:
                user = User.objects.create_user(
                    email=email,
                    password=self.USER_PASSWORD,
                    username=f"user{i}",
                    phone_number=fake.numerify("+7##########"),
                    city=fake.city(),
                )
                created += 1
            users.append(user)
        return users, created
