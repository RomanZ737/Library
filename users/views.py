from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from .models import CustomUser
from .permissions import IsOwner
from .serializers import CustomUserSerializer
from rest_framework import viewsets


class CustomUserViewSet(viewsets.ModelViewSet):
    serializer_class = CustomUserSerializer
    queryset = CustomUser.objects.all()

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy'):
            return [IsOwner()]
        return super().get_permissions()


class UserCreateAPIView(CreateAPIView):
    serializer_class = CustomUserSerializer
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
