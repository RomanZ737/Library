from django.contrib import admin
from .models import Author, Book, BookMark, BookRent


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'middle_name', 'date_of_birth', 'comment')
    list_filter = ('date_of_birth', 'last_name')
    search_fields = ('first_name', 'last_name', 'comment')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'release_date', 'is_rented', 'genre', 'total_mark')
    list_filter = ('author', 'release_date', 'is_rented', 'genre')
    search_fields = ('name', 'author__first_name', 'author__last_name', 'annotation')


# @admin.register(BookMark)
# class BookMarkAdmin(admin.ModelAdmin):
#     list_display = ('book', 'user', 'mark')
#     list_filter = ('book', 'user', 'mark')
#     search_fields = ('book', 'user', 'mark')


@admin.register(BookRent)
class BookRentAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rented_date', 'rented_date_end', 'comment')
    list_filter = ('book', 'user')
    search_fields = ('book__name', 'user__email', 'comment')
