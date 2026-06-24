from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_USER = "user"
    ROLE_ADMIN = "admin"
    ROLE_CHOICES = [
        (ROLE_USER, "일반 사용자"),
        (ROLE_ADMIN, "관리자"),
    ]

    name = models.CharField("이름", max_length=100, blank=True)
    email = models.EmailField("이메일", unique=True)
    role = models.CharField("역할", max_length=10, choices=ROLE_CHOICES, default=ROLE_USER)
    department = models.CharField("부서", max_length=100, blank=True)
    title = models.CharField("직책", max_length=100, blank=True)
    phone = models.CharField("연락처", max_length=30, blank=True)

    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "User"

    def display_name(self):
        return self.name or self.username
