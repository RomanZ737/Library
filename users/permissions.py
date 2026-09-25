from rest_framework.permissions import BasePermission
from django.contrib.auth.models import Group

class IsOwner(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.user == obj:
            return True
        return False

class IsAdminGroup(BasePermission):

    def has_permission(self, request, view):
        return True if (request.user.is_superuser or
                        request.user.groups.filter(name='Администраторы').exists()) else False
