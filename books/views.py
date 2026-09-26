from rest_framework import viewsets, views
from rest_framework.response import Response
from django.db import IntegrityError
from .models import Book, Author, BookMark, BookRent
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import (
    BookSerializer,
    AuthorSerializer,
    BookMarkSerializer,
    BookMarkUpdateSerializer,
    BookRentSerializer,
)
from .pagination import BookPagination, AuthorPagination
from users.permissions import IsAdminGroup
from rest_framework import generics
from .services import (
    create_bookmark,
    update_bookmark,
    delete_bookmark,
    create_book_rent,
    close_book_rent,
    BookAlreadyRented,
    BookNotRented,
)
from django.shortcuts import get_object_or_404


BOOK_ID_PARAM = openapi.Parameter(
    'book_id', openapi.IN_PATH,
    type=openapi.TYPE_INTEGER,
    description='ID книги',
)


class BookViewSet(viewsets.ModelViewSet):
    serializer_class = BookSerializer
    queryset = Book.objects.all()
    pagination_class = BookPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["genre", "is_rented", "author"]
    search_fields = ["name", "author__last_name", "author__first_name", "annotation"]
    ordering_fields = ["name", "release_date", "total_mark", "number_of_marks"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsAdminGroup()]
        return [IsAuthenticated()]


class BookMarkCreate(generics.CreateAPIView):
    serializer_class = BookMarkSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        book = serializer.validated_data["book"]
        mark = serializer.validated_data["mark"]

        try:
            bookmark = create_bookmark(request.user, book.id, mark)
        except IntegrityError:
            return Response({"detail": "Вы уже оценили эту книгу."}, status=400)

        out = self.get_serializer(bookmark)
        return Response(out.data, status=201)


class BookMarkUpdate(generics.UpdateAPIView):
    serializer_class = BookMarkSerializer
    queryset = BookMark.objects.all()
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        book_mark = self.get_object()
        serializer = self.get_serializer(book_mark, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        mark = serializer.validated_data["mark"]
        new_bookmark = update_bookmark(book_mark, mark)
        out = self.get_serializer(new_bookmark)
        return Response(out.data, status=200)

    def get_queryset(self):
        return BookMark.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        return BookMarkUpdateSerializer


class BookMarkDelete(generics.DestroyAPIView):
    serializer_class = BookMarkSerializer
    queryset = BookMark.objects.all()
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        book_mark = self.get_object()
        delete_bookmark(book_mark)
        return Response(status=204)

    def get_queryset(self):
        return BookMark.objects.filter(user=self.request.user)


class AuthorViewSet(viewsets.ModelViewSet):
    serializer_class = AuthorSerializer
    queryset = Author.objects.all()
    pagination_class = AuthorPagination
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsAdminGroup()]
        return [IsAuthenticated()]


class BookRentView(views.APIView):

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsAdminGroup()]
        return [IsAuthenticated()]

    @swagger_auto_schema(
        operation_summary='Выдать книгу',
        operation_description='Создаёт аренду для книги. Срок — 30 дней по умолчанию, максимум 60.',
        manual_parameters=[BOOK_ID_PARAM],
        request_body=BookRentSerializer,
        responses={
            201: BookRentSerializer,
            400: 'Книга уже выдана или некорректная дата',
            404: 'Книга не найдена',
        },
    )
    def post(self, request, book_id):
        get_object_or_404(Book, pk=book_id)

        serializer = BookRentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rented_date_end = serializer.validated_data.get("rented_date_end")
        comment = serializer.validated_data.get("comment")

        try:
            book_rent = create_book_rent(
                user=request.user,
                book_id=book_id,
                rented_date_end=rented_date_end,
                comment=comment,
            )
        except BookAlreadyRented as e:
            return Response({"detail": str(e)}, status=400)

        out = BookRentSerializer(book_rent)
        return Response(out.data, status=201)

    @swagger_auto_schema(
        operation_summary='Активная аренда книги',
        manual_parameters=[BOOK_ID_PARAM],
        responses={
            200: BookRentSerializer,
            404: 'У книги нет активной аренды',
        },
    )
    def get(self, request, book_id):
        get_object_or_404(Book, pk=book_id)

        book_rent = BookRent.objects.filter(book_id=book_id).first()
        if book_rent is None:
            return Response({"detail": "У книги нет активной аренды."}, status=404)

        out = BookRentSerializer(book_rent)
        return Response(out.data, status=200)

    @swagger_auto_schema(
        operation_summary='Вернуть книгу',
        operation_description='Доступно только администраторам.',
        manual_parameters=[BOOK_ID_PARAM],
        responses={
            200: BookRentSerializer,
            400: 'У книги нет активной аренды',
            403: 'Только администратор может вернуть книгу',
        },
    )
    def delete(self, request, book_id):
        get_object_or_404(Book, pk=book_id)

        try:
            book_rent = close_book_rent(book_id)
        except BookNotRented as e:
            return Response({"detail": str(e)}, status=400)

        out = BookRentSerializer(book_rent)
        return Response(out.data, status=200)
