from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import User, VPNClient, UserNetwork, RegistrationSettings


@admin.register(RegistrationSettings)
class RegistrationSettingsAdmin(admin.ModelAdmin):
    list_display = ['get_status']

    def get_status(self, obj):
        return str(obj)
    get_status.short_description = "Статус регистрации"

    def has_add_permission(self, request):
        # Запрещаем создание новых записей (singleton)
        return False

    def has_delete_permission(self, request, obj=None):
        # Запрещаем удаление
        return False

    change_form_template = 'admin/registration_settings_change_form.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('open-timed/', self.admin_site.admin_view(self.open_timed), name='registration_open_timed'),
            path('open-unlimited/', self.admin_site.admin_view(self.open_unlimited), name='registration_open_unlimited'),
            path('close/', self.admin_site.admin_view(self.close_registration), name='registration_close'),
        ]
        return custom_urls + urls

    def open_timed(self, request):
        minutes = request.POST.get('minutes', 30)
        try:
            minutes = int(minutes)
            settings = RegistrationSettings.get_settings()
            settings.is_open = True
            settings.closes_at = timezone.now() + timedelta(minutes=minutes)
            settings.save()
            messages.success(request, f"Регистрация открыта на {minutes} минут")
        except ValueError:
            messages.error(request, "Неверное значение минут")
        return redirect('admin:core_registrationsettings_changelist')

    def open_unlimited(self, request):
        settings = RegistrationSettings.get_settings()
        settings.is_open = True
        settings.closes_at = None
        settings.save()
        messages.success(request, "Регистрация открыта бессрочно")
        return redirect('admin:core_registrationsettings_changelist')

    def close_registration(self, request):
        settings = RegistrationSettings.get_settings()
        settings.is_open = False
        settings.closes_at = None
        settings.save()
        messages.success(request, "Регистрация закрыта")
        return redirect('admin:core_registrationsettings_changelist')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'is_approved', 'is_staff', 'is_superuser', 'date_joined']
    list_filter = ['is_approved', 'is_staff', 'is_superuser']
    search_fields = ['username']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Статус', {'fields': ('is_approved', 'is_active', 'is_staff', 'is_superuser')}),
        ('Права доступа', {'fields': ('groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(UserNetwork)
class UserNetworkAdmin(admin.ModelAdmin):
    list_display = ['user', 'subnet', 'created_at']
    search_fields = ['user__username', 'subnet']
    readonly_fields = ['created_at']


@admin.register(VPNClient)
class VPNClientAdmin(admin.ModelAdmin):
    list_display = ['user', 'certificate_name', 'created_at', 'is_active']
    search_fields = ['user__username', 'certificate_name']
    readonly_fields = ['created_at']
