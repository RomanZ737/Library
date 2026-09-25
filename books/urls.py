from .views import BookViewSet, AuthorViewSet, BookMarkCreate, BookMarkUpdate, BookMarkDelete, BookRentView
from rest_framework.routers import DefaultRouter
from .apps import BooksConfig

from django.urls import path

app_name = BooksConfig.name

router = DefaultRouter()
router.register(r'books', BookViewSet, basename='books')
router.register(r'authors', AuthorViewSet, basename='authors')

urlpatterns = [
      path('books/marks/', BookMarkCreate.as_view(), name='bookmark-create'),
      path('books/marks/update/<int:pk>/', BookMarkUpdate.as_view(), name='bookmark-update'),
      path('books/marks/delete/<int:pk>/', BookMarkDelete.as_view(), name='bookmark-delete'),
      path('books/<int:book_id>/rent/', BookRentView.as_view(), name='book-rent')
              ] + router.urls
