from rest_framework import serializers
from .models import Book, Author, BookMark, BookRent
from .validators import validate_book_return_date


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['name', 'author', 'release_date', 'genre', 'annotation', 'total_mark',
                  'is_rented', 'id', 'number_of_marks', 'mark_summ']
        read_only_fields = ['total_mark', 'is_rented', 'number_of_marks', 'mark_summ']


class AuthorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Author
        fields = '__all__'


class BookMarkSerializer(serializers.ModelSerializer):

    class Meta:
        model = BookMark
        fields = ['book', 'mark', 'id']
        read_only_fields = ['id']


class BookMarkUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookMark
        fields = ['id', 'book', 'mark']
        read_only_fields = ['id', 'book']


class BookRentSerializer(serializers.ModelSerializer):
    rented_date_end = serializers.DateField(validators=[validate_book_return_date], required=False)

    class Meta:
        model = BookRent
        fields = ['id', 'book', 'user', 'rented_date', 'rented_date_end', 'comment']
        read_only_fields = ['id', 'book', 'user', 'rented_date']
