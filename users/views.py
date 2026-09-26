from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from .models import CustomUser
from .permissions import IsOwner
from .serializers import CustomUserSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated


class CustomUserViewSet(viewsets.ModelViewSet):
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOwner()]
        return super().get_permissions()

    def get_queryset(self):
        if self.request.user.groups.filter(name="Администраторы").exists():
            queryset = CustomUser.objects.all()
        else:
            queryset = CustomUser.objects.filter(pk=self.request.user.pk)
        return queryset


class UserCreateAPIView(CreateAPIView):
    serializer_class = CustomUserSerializer
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
