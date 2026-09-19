import random

from django.core.management.base import BaseCommand
from users.models import CustomUser, Payments
from lms.models import Lesson, Course
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Add users, payments, lessons and courses for testing'

    def handle(self, *args, **kwargs):
        # Данные внутри метода
        users = [
            {
                'email': 'test_user_1@example.com',
                'password': 'user12345@',
                'city': 'Moscow',
                'phone_number': '+79991111111'
            },
            {
                'email': 'test_user_2@example.com',
                'password': 'user12345@',
                'city': 'St. Petersburg',
                'phone_number': '+79992222222'
            },
            {
                'email': 'test_user_3@example.com',
                'password': 'user12345@',
                'city': 'Kazan',
                'phone_number': '+79993333333'
            },
        ]

        moderator = {
                'email': 'moderator_user@example.com',
                'password': 'Moderator12345@',
                'city': 'Moscow',
                'phone_number': '+79994444444'
        }

        courses = [
            {'name': 'Python Basics', 'description': 'Основы программирования на Python', 'price': 100},
            {'name': 'Django Course', 'description': 'Веб-разработка на Django', 'price': 200},
            {'name': 'DRF Advanced', 'description': 'Продвинутый Django REST Framework', 'price': 300},
        ]

        lessons = [
            {'name': 'Lesson 1: Introduction', 'description': 'Введение в тему', 'price': 50},
            {'name': 'Lesson 2: Setup', 'description': 'Настройка окружения', 'price': 60},
            {'name': 'Lesson 3: Basics', 'description': 'Базовые концепции', 'price': 70},
            {'name': 'Lesson 4: Practice', 'description': 'Практическое задание', 'price': 80},
            {'name': 'Lesson 5: Advanced', 'description': 'Продвинутые темы', 'price': 90},
        ]

        # === Очистка (кроме пользователей) ===
        self.stdout.write(self.style.WARNING('Очистка платежей, уроков и курсов...'))
        Payments.objects.all().delete()
        Lesson.objects.all().delete()
        Course.objects.all().delete()
        Group.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Платежи, уроки и курсы удалены!'))

        # === Создание или получение пользователей, групп и модератора===
        moderator_group = Group.objects.create(name='Moderators')
        created_users = []
        for user_data in users:
            email = user_data.pop('email')
            if not CustomUser.objects.filter(email=email).exists():
                user = CustomUser.objects.create_user(
                    email=email,
                    **user_data
                )
                self.stdout.write(self.style.SUCCESS(f'Пользователь создан: {user.email}'))
            else:
                user = CustomUser.objects.get(email=email)
                self.stdout.write(self.style.WARNING(f'Пользователь {email} уже существует'))
            created_users.append(user)

        # Создаём модератора
        if not CustomUser.objects.filter(email=moderator['email']).exists():
            moderator_user = CustomUser.objects.create_user(
                **moderator
            )
            moderator_user.groups.add(moderator_group)
            moderator_user.save()

        #  Создание курсов
        created_courses = []
        for course_data in courses:
            course = Course.objects.create(**course_data)
            course.owner = random.choice(created_users)
            course.save()
            created_courses.append(course)
            self.stdout.write(self.style.SUCCESS(f'Курс создан: {course.name}'))

        # Создание уроков
        created_lessons = []
        for i, lesson_data in enumerate(lessons):
            course = created_courses[i % len(created_courses)]
            lesson = Lesson.objects.create(
                course=course,
                **lesson_data
            )
            lesson.owner = random.choice(created_users)
            lesson.save()
            created_lessons.append(lesson)
            self.stdout.write(
                self.style.SUCCESS(f'Урок создан: {lesson.name} (курс: {course.name})')
            )

        # Создание платежей
        payment_count = 0
        payment_methods = ['Cash', 'Transfer']

        for i, student in enumerate(created_users):
            course_index = i % len(created_courses)
            course = created_courses[course_index]

            payment_method = payment_methods[i % len(payment_methods)]

            payment_date = timezone.now() - timedelta(days=i * 3, hours=i * 5)

            if not Payments.objects.filter(
                    user=student,
                    payed_course=course
            ).exists():
                Payments.objects.create(
                    user=student,
                    payed_course=course,
                    payed_lesson=created_lessons[0],
                    payment_amount=15000 + i * 1000,
                    payment_method=payment_method,
                    payment_at=payment_date,
                )
                payment_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Платёж за курс: {student.email} → {course.name} '
                        f'({payment_method}, {payment_date.strftime("%d.%m.%Y %H:%M")})'
                    )
                )

            lesson_index = (i * 2) % len(created_lessons)

            second_payment_method = payment_methods[(i + 1) % len(payment_methods)]
            second_payment_date = timezone.now() - timedelta(days=i * 2 + 1, hours=i * 3)

            if not Payments.objects.filter(
                    user=student,
                    payed_lesson=created_lessons[lesson_index]
            ).exists():
                Payments.objects.create(
                    user=student,
                    payed_course=created_lessons[lesson_index].course,
                    payed_lesson=created_lessons[lesson_index],
                    payment_amount=5000 + i * 500,
                    payment_method=second_payment_method,
                    payment_at=second_payment_date,
                )
                payment_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Платёж за урок: {student.email} → {created_lessons[lesson_index].name} '
                        f'({second_payment_method}, {second_payment_date.strftime("%d.%m.%Y %H:%M")})'
                    )
                )

        # === Итоговая статистика ===
        self.stdout.write(self.style.SUCCESS(
            f'\n{"-" * 10}\n'
            f'База данных наполнена!\n'
            f'Пользователей: {len(created_users)}\n'
            f'Курсов: {len(created_courses)}\n'
            f'Уроков: {len(created_lessons)}\n'
            f'Платежей: {payment_count}\n'
            f'{"-" * 10}'
        ))
