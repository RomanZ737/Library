from datetime import timedelta

from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.test import APITestCase

from books.factories import create_admin, create_author, create_book, create_user
from books.models import Book, BookGenre, BookMark, BookRent
from books.services import (
    BookAlreadyRented,
    BookNotRented,
    close_book_rent,
    create_book_rent,
    create_bookmark,
    delete_bookmark,
    update_bookmark,
)
from books.validators import validate_book_return_date


# ---------- Services ----------

class BookMarkServicesTest(TestCase):

    def setUp(self):
        self.user1 = create_user(email='u1@test.com')
        self.user2 = create_user(email='u2@test.com')
        self.book = create_book()

    def test_create_bookmark_updates_book_aggregates(self):
        create_bookmark(self.user1, self.book.id, 5)
        self.book.refresh_from_db()
        self.assertEqual(self.book.number_of_marks, 1)
        self.assertEqual(self.book.mark_summ, 5)
        self.assertEqual(self.book.total_mark, 5.0)

    def test_create_two_bookmarks_average(self):
        create_bookmark(self.user1, self.book.id, 4)
        create_bookmark(self.user2, self.book.id, 2)
        self.book.refresh_from_db()
        self.assertEqual(self.book.number_of_marks, 2)
        self.assertEqual(self.book.mark_summ, 6)
        self.assertEqual(self.book.total_mark, 3.0)

    def test_create_bookmark_duplicate_raises(self):
        create_bookmark(self.user1, self.book.id, 5)
        with self.assertRaises(IntegrityError):
            create_bookmark(self.user1, self.book.id, 3)

    def test_update_bookmark_recalculates_total(self):
        bm = create_bookmark(self.user1, self.book.id, 5)
        update_bookmark(bm, 3)
        self.book.refresh_from_db()
        self.assertEqual(bm.mark, 3)
        self.assertEqual(self.book.mark_summ, 3)
        self.assertEqual(self.book.total_mark, 3.0)

    def test_update_bookmark_average_with_two(self):
        bm1 = create_bookmark(self.user1, self.book.id, 5)
        create_bookmark(self.user2, self.book.id, 1)
        update_bookmark(bm1, 3)
        self.book.refresh_from_db()
        self.assertEqual(self.book.mark_summ, 4)
        self.assertEqual(self.book.total_mark, 2.0)

    def test_delete_bookmark_when_last_resets_total(self):
        bm = create_bookmark(self.user1, self.book.id, 5)
        delete_bookmark(bm)
        self.book.refresh_from_db()
        self.assertEqual(self.book.number_of_marks, 0)
        self.assertEqual(self.book.mark_summ, 0)
        self.assertEqual(self.book.total_mark, 0)

    def test_delete_bookmark_with_remaining(self):
        bm1 = create_bookmark(self.user1, self.book.id, 5)
        create_bookmark(self.user2, self.book.id, 3)
        delete_bookmark(bm1)
        self.book.refresh_from_db()
        self.assertEqual(self.book.number_of_marks, 1)
        self.assertEqual(self.book.total_mark, 3.0)


class BookRentServicesTest(TestCase):

    def setUp(self):
        self.user = create_user(email='rent@test.com')
        self.book = create_book()

    def test_create_book_rent_sets_flag(self):
        rent = create_book_rent(self.user, self.book.id)
        self.book.refresh_from_db()
        self.assertTrue(self.book.is_rented)
        self.assertEqual(rent.book_id, self.book.id)
        self.assertEqual(rent.user_id, self.user.id)
        self.assertEqual(rent.rented_date, timezone.localdate())
        self.assertEqual((rent.rented_date_end - rent.rented_date).days, 30)

    def test_create_book_rent_custom_date(self):
        custom_end = timezone.localdate() + timedelta(days=45)
        rent = create_book_rent(self.user, self.book.id, rented_date_end=custom_end)
        self.assertEqual(rent.rented_date_end, custom_end)

    def test_create_book_rent_on_rented_raises(self):
        create_book_rent(self.user, self.book.id)
        with self.assertRaises(BookAlreadyRented):
            create_book_rent(self.user, self.book.id)

    def test_close_book_rent(self):
        create_book_rent(self.user, self.book.id)
        closed = close_book_rent(self.book.id)
        self.book.refresh_from_db()
        self.assertFalse(self.book.is_rented)
        self.assertEqual(BookRent.objects.filter(book=self.book).count(), 0)
        self.assertIsNotNone(closed.pk)

    def test_close_book_rent_without_active_raises(self):
        with self.assertRaises(BookNotRented):
            close_book_rent(self.book.id)


# ---------- Validators ----------

class ValidateReturnDateTest(TestCase):

    def test_valid_date_30_days(self):
        target = timezone.localdate() + timedelta(days=30)
        self.assertEqual(validate_book_return_date(target), target)

    def test_valid_date_60_days(self):
        target = timezone.localdate() + timedelta(days=60)
        self.assertEqual(validate_book_return_date(target), target)

    def test_date_over_60_raises(self):
        target = timezone.localdate() + timedelta(days=61)
        with self.assertRaises(serializers.ValidationError):
            validate_book_return_date(target)

    def test_date_today_raises(self):
        with self.assertRaises(serializers.ValidationError):
            validate_book_return_date(timezone.localdate())

    def test_date_in_past_raises(self):
        target = timezone.localdate() - timedelta(days=1)
        with self.assertRaises(serializers.ValidationError):
            validate_book_return_date(target)


# ---------- Books views ----------

class BookViewSetTest(APITestCase):

    def setUp(self):
        self.user = create_user()
        self.admin = create_admin()
        self.author = create_author()
        self.book = create_book(author=self.author, name='Война и мир')
        self.other_book = create_book(
            author=self.author, name='Преступление и наказание',
            genre=BookGenre.MYSTERY,
        )
        self.url = reverse('books:books-list')

    def test_list_requires_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_authenticated(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_search_by_name(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, {'search': 'Война'})
        self.assertEqual(response.data['count'], 1)

    def test_search_by_author(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, {'search': 'Иванов'})
        self.assertEqual(response.data['count'], 2)

    def test_filter_by_genre(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, {'genre': BookGenre.MYSTERY})
        self.assertEqual(response.data['count'], 1)

    def test_filter_by_is_rented(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, {'is_rented': 'false'})
        self.assertEqual(response.data['count'], 2)

    def test_create_forbidden_for_regular_user(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, {
            'name': 'Новая',
            'author': self.author.id,
            'release_date': '2021-01-01',
            'genre': BookGenre.FICTION,
            'annotation': 'aaa',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_allowed_for_admin(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(self.url, {
            'name': 'Новая',
            'author': self.author.id,
            'release_date': '2021-01-01',
            'genre': BookGenre.FICTION,
            'annotation': 'aaa',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 3)

    def test_delete_forbidden_for_regular_user(self):
        self.client.force_authenticate(self.user)
        url = reverse('books:books-detail', args=[self.book.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_allowed_for_admin(self):
        self.client.force_authenticate(self.admin)
        url = reverse('books:books-detail', args=[self.book.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


# ---------- Marks views ----------

class BookMarkViewTest(APITestCase):

    def setUp(self):
        self.user = create_user(email='u1@test.com')
        self.other = create_user(email='u2@test.com')
        self.book = create_book()

    def test_create_mark(self):
        self.client.force_authenticate(self.user)
        url = reverse('books:bookmark-create')
        response = self.client.post(url, {'book': self.book.id, 'mark': 5})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.book.refresh_from_db()
        self.assertEqual(self.book.total_mark, 5.0)
        self.assertTrue(BookMark.objects.filter(user=self.user, book=self.book).exists())

    def test_create_mark_twice_returns_400(self):
        self.client.force_authenticate(self.user)
        url = reverse('books:bookmark-create')
        self.client.post(url, {'book': self.book.id, 'mark': 5})
        response = self.client.post(url, {'book': self.book.id, 'mark': 4})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_mark_invalid_value(self):
        self.client.force_authenticate(self.user)
        url = reverse('books:bookmark-create')
        response = self.client.post(url, {'book': self.book.id, 'mark': 10})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_own_mark(self):
        self.client.force_authenticate(self.user)
        self.client.post(reverse('books:bookmark-create'), {'book': self.book.id, 'mark': 5})
        bm = BookMark.objects.get(user=self.user, book=self.book)
        url = reverse('books:bookmark-update', args=[bm.id])
        response = self.client.patch(url, {'mark': 3})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.total_mark, 3.0)

    def test_update_other_user_mark_returns_404(self):
        self.client.force_authenticate(self.other)
        self.client.post(reverse('books:bookmark-create'), {'book': self.book.id, 'mark': 5})
        bm = BookMark.objects.get(user=self.other, book=self.book)
        self.client.force_authenticate(self.user)
        url = reverse('books:bookmark-update', args=[bm.id])
        response = self.client.patch(url, {'mark': 3})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_own_mark(self):
        self.client.force_authenticate(self.user)
        self.client.post(reverse('books:bookmark-create'), {'book': self.book.id, 'mark': 5})
        bm = BookMark.objects.get(user=self.user, book=self.book)
        url = reverse('books:bookmark-delete', args=[bm.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.book.refresh_from_db()
        self.assertEqual(self.book.total_mark, 0)

    def test_delete_other_user_mark_returns_404(self):
        self.client.force_authenticate(self.other)
        self.client.post(reverse('books:bookmark-create'), {'book': self.book.id, 'mark': 5})
        bm = BookMark.objects.get(user=self.other, book=self.book)
        self.client.force_authenticate(self.user)
        url = reverse('books:bookmark-delete', args=[bm.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------- Rents views ----------

class BookRentViewTest(APITestCase):

    def setUp(self):
        self.user = create_user(email='rent_u@test.com')
        self.admin = create_admin()
        self.book = create_book()

    def _url(self, book_id=None):
        return reverse('books:book-rent', args=[book_id or self.book.id])

    def test_post_requires_auth(self):
        response = self.client.post(self._url(), {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_creates_rent(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self._url(), {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.book.refresh_from_db()
        self.assertTrue(self.book.is_rented)

    def test_post_with_custom_date(self):
        self.client.force_authenticate(self.user)
        end = (timezone.localdate() + timedelta(days=45)).isoformat()
        response = self.client.post(self._url(), {'rented_date_end': end})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_with_invalid_date(self):
        self.client.force_authenticate(self.user)
        end = (timezone.localdate() + timedelta(days=100)).isoformat()
        response = self.client.post(self._url(), {'rented_date_end': end})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_on_rented_book_returns_400(self):
        self.client.force_authenticate(self.user)
        self.client.post(self._url(), {})
        response = self.client.post(self._url(), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_nonexistent_book_404(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self._url(book_id=99999), {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_returns_active_rent(self):
        self.client.force_authenticate(self.user)
        self.client.post(self._url(), {})
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['book'], self.book.id)

    def test_get_no_rent_404(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_forbidden_for_regular_user(self):
        self.client.force_authenticate(self.user)
        self.client.post(self._url(), {})
        response = self.client.delete(self._url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_allowed_for_admin(self):
        self.client.force_authenticate(self.user)
        self.client.post(self._url(), {})
        self.client.force_authenticate(self.admin)
        response = self.client.delete(self._url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertFalse(self.book.is_rented)
        self.assertEqual(BookRent.objects.count(), 0)

    def test_delete_no_rent_400(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(self._url())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
