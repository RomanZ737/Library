from django.db import transaction
from .models import Book, BookMark, BookRent


@transaction.atomic
def create_bookmark(user, book_id, mark):
    book = Book.objects.select_for_update().get(pk=book_id)

    bookmark = BookMark.objects.create(user=user, book=book, mark=mark)

    book.number_of_marks += 1
    book.mark_summ += mark
    book.total_mark = book.mark_summ / book.number_of_marks
    book.save(update_fields=["number_of_marks", "mark_summ", "total_mark"])

    return bookmark


@transaction.atomic
def update_bookmark(bookmark, new_mark):
    book = Book.objects.select_for_update().get(pk=bookmark.book_id)
    old_mark = bookmark.mark

    bookmark.mark = new_mark
    bookmark.save(update_fields=["mark"])

    book.mark_summ = book.mark_summ - old_mark + new_mark
    book.total_mark = book.mark_summ / book.number_of_marks
    book.save(update_fields=["mark_summ", "total_mark"])

    return bookmark


@transaction.atomic
def delete_bookmark(bookmark):
    book = Book.objects.select_for_update().get(pk=bookmark.book_id)
    mark = bookmark.mark

    bookmark.delete()

    book.number_of_marks -= 1
    book.mark_summ -= mark
    if book.number_of_marks > 0:
        book.total_mark = book.mark_summ / book.number_of_marks
    else:
        book.total_mark = 0  # ← либо None, если ты так решишь

    book.save(update_fields=["number_of_marks", "mark_summ", "total_mark"])


class BookAlreadyRented(Exception):
    """У книги уже есть активная аренда."""

    pass


class BookNotRented(Exception):
    """У книги нет активной аренды."""

    pass


@transaction.atomic
def create_book_rent(user, book_id, rented_date_end=None, comment=None):
    book = Book.objects.select_for_update().get(pk=book_id)

    if book.is_rented:
        raise BookAlreadyRented("Книга уже выдана.")

    rent_kwargs = {
        "book": book,
        "user": user,
        "comment": comment,
    }
    if rented_date_end is not None:
        rent_kwargs["rented_date_end"] = rented_date_end

    book_rent = BookRent.objects.create(**rent_kwargs)

    book.is_rented = True
    book.save(update_fields=["is_rented"])

    return book_rent


@transaction.atomic
def close_book_rent(book_id):
    book = Book.objects.select_for_update().get(pk=book_id)

    book_rent = BookRent.objects.filter(book=book).first()
    if book_rent is None:
        raise BookNotRented("У книги нет активной аренды.")

    rent_id = book_rent.pk
    book_rent.delete()
    book_rent.pk = rent_id

    book.is_rented = False
    book.save(update_fields=["is_rented"])

    return book_rent
