from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models

class User(AbstractUser):
    is_approved = models.BooleanField(
        default=False,
        verbose_name="Одобрен администратором"
    )
    full_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ФИО"
    )
    group = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Группа"
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class VPNClient(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='vpn_client'
    )
    certificate_name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"VPN for {self.user.username}"

class UserNetwork(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='network'
    )
    subnet = models.CharField(max_length=18, unique=True)  # например "10.100.67.0/24"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} → {self.subnet}"
