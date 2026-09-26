from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Поля в таблице пользователей
    list_display = (
        "email",
        "phone_number",
        "city",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_filter = ("is_active", "is_staff", "is_superuser")

    search_fields = ("email", "phone_number", "city")

    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Личная информация", {"fields": ("phone_number", "city", "avatar")}),
        (
            "Разрешения",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Важные даты", {"fields": ("last_login", "date_joined")}),
    )

    # Поля в форме создания нового пользователя
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
