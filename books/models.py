from django.db import models
from users.models import CustomUser


class BookGenders(models.TextChoices):
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


class Book(models.Model):
    name = models.CharField(max_length=100, verbose_name='Book Name', help_text='Название книги')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, verbose_name='Author', help_text='Автор Книги')
    release_date = models.DateField(verbose_name='Book release date', help_text='Дата публикации книги')
    is_rented = models.BooleanField(verbose_name='Book is rented', default=False, help_text='Книга в аренде')
    genre = models.CharField(max_length=100, choices=BookGenders.choices, default=BookGenders.FICTION,
                             verbose_name='Genre', help_text='Жанр книги')
    annotation = models.TextField()

    class Meta:
        ordering = ['name']
        verbose_name = "Книга"
        verbose_name_plural = "Книги"


class BookMark(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name='Book', help_text='Книга')
    number_of_marks = models.IntegerField(default=0, verbose_name='Marks Count', help_text='Количество оценок')
    mark_summ = models.IntegerField(default=0, verbose_name='Summ og Marks', help_text='Количество оценок')
    total_mark = models.IntegerField(default=0, verbose_name='Total Mark', help_text='Общая оценка (средняя)')

    class Meta:
        ordering = ['total_mark']
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"


class BookRent(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name='Book', help_text='Книга')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='User', help_text='Пользователь')
    rented_date = models.DateField(verbose_name='Rent start Date', help_text='Дата начала аренды')
    rented_date_end = models.DateField(verbose_name='Rent end Date', help_text='Дата окончания аренды')
    comment = models.TextField(verbose_name='Comment', help_text='Комментарий')

    class Meta:
        ordering = ['book']
        verbose_name = "Арендованная книга"
        verbose_name_plural = "Арендованные книги"
        unique_together = ('user', 'book')