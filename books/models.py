from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from users.models import CustomUser
from django.utils import timezone


class BookGenre(models.TextChoices):
    FICTION = 'FICTION', 'Художественная литература'
    NON_FICTION = 'NON_FICTION', 'Нехудожественная литература'
    FANTASY = 'FANTASY', 'Фэнтези'
    SCIENCE_FICTION = 'SCIENCE_FICTION', 'Научная фантастика'
    MYSTERY = 'MYSTERY', 'Детектив'
    THRILLER = 'THRILLER', 'Триллер'
    ROMANCE = 'ROMANCE', 'Любовный роман'
    HORROR = 'HORROR', 'Ужасы'
    ADVENTURE = 'ADVENTURE', 'Приключения'
    BIOGRAPHY = 'BIOGRAPHY', 'Биография'


class Author(models.Model):
    first_name = models.CharField(max_length=100, verbose_name='First Name', help_text='Имя Автора')
    last_name = models.CharField(max_length=100, verbose_name='Last Name', help_text='Фамилия Автора')
    middle_name = models.CharField(max_length=100, null=True, blank=True,
                                   verbose_name='Middle Name', help_text='Отчество Автора')
    date_of_birth = models.DateField(verbose_name='Date of Birth', help_text='Дата рождения Автора')
    comment = models.TextField(verbose_name='Comment', null=True, blank=True, help_text='Комментарий к автору')

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = "Автор"
        verbose_name_plural = "Авторы"

    def __str__(self):
        return f'{self.last_name} {self.first_name}'


class Book(models.Model):
    name = models.CharField(max_length=100, verbose_name='Book Name', help_text='Название книги')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, verbose_name='Author', help_text='Автор Книги')
    release_date = models.DateField(verbose_name='Book release date', help_text='Дата публикации книги')
    is_rented = models.BooleanField(verbose_name='Book is rented', default=False, help_text='Книга в аренде')
    genre = models.CharField(max_length=100, choices=BookGenre.choices, default=BookGenre.FICTION,
                             verbose_name='Genre', help_text='Жанр книги')
    number_of_marks = models.IntegerField(default=0, verbose_name='Marks Count', help_text='Количество оценок')
    mark_summ = models.IntegerField(default=0, verbose_name='Summ of Marks', help_text='Сумма оценок')
    total_mark = models.FloatField(default=0, verbose_name='Total Mark', help_text='Общая оценка (средняя)')
    annotation = models.TextField(verbose_name='Annotation', help_text='Аннотация книги')

    class Meta:
        ordering = ['name']
        verbose_name = "Книга"
        verbose_name_plural = "Книги"

    def __str__(self):
        return f'{(self.name).upper()}\n{self.author.last_name} {self.author.first_name}'


class BookMark(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name='Book', help_text='Книга')
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, verbose_name='User',
                             help_text='Пользователь', null=True, blank=True)
    mark = models.IntegerField(verbose_name='Mark', help_text='Оценка',
                               validators=[MinValueValidator(0), MaxValueValidator(5)], default=0)

    class Meta:
        ordering = ['book__name']
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"
        constraints = [models.UniqueConstraint(fields=['user', 'book'], name='unique_mark_per_user_book')]

    def __str__(self):
        return f'{self.user} → {self.book}: {self.mark}'


class BookRent(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name='Book', help_text='Книга')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='User', help_text='Пользователь')
    rented_date = models.DateField(verbose_name='Rent start Date',
                                   help_text='Дата начала аренды', default=timezone.localdate)
    rented_date_end = models.DateField(verbose_name='Rent end Date', help_text='Дата окончания аренды')
    comment = models.TextField(verbose_name='Comment', help_text='Комментарий', null=True, blank=True)

    class Meta:
        ordering = ['book']
        verbose_name = "Арендованная книга"
        verbose_name_plural = "Арендованные книги"
        constraints = [models.UniqueConstraint(fields=['book'], name='unique_active_rent_per_book')]

    def __str__(self):
        return (f'{(self.book.name).upper()}\n '
                f'Дата начала: {self.rented_date}\n Дата окончания: {self.rented_date_end}')