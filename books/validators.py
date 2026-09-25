from django.utils import timezone
from rest_framework import serializers


def validate_book_return_date(return_date):
    delta = (return_date - timezone.localdate()).days
    if delta > 60:
        raise serializers.ValidationError('Дата возврата книги слишком большая')
    elif delta < 1:
        raise serializers.ValidationError('Минимальный срок аренды — 1 день')
    return return_date