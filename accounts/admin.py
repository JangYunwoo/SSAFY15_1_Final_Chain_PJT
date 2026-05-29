from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class WaferUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("업무 정보", {"fields": ("name", "role", "department", "title", "phone")}),)
    list_display = ("username", "name", "email", "department", "title", "role", "is_active")
    list_filter = ("role", "department", "is_active")
