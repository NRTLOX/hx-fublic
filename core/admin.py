from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import User, VPNClient, UserNetwork, RegistrationSettings


class RegistrationSettingsAdmin(admin.ModelAdmin):
    """Админка для управления регистрацией через кнопки на главной странице админки"""

    def has_module_permission(self, request):
        # Скрываем из списка моделей в админке
        return False

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
        return redirect('admin:index')

    def open_unlimited(self, request):
        settings = RegistrationSettings.get_settings()
        settings.is_open = True
        settings.closes_at = None
        settings.save()
        messages.success(request, "Регистрация открыта бессрочно")
        return redirect('admin:index')

    def close_registration(self, request):
        settings = RegistrationSettings.get_settings()
        settings.is_open = False
        settings.closes_at = None
        settings.save()
        messages.success(request, "Регистрация закрыта")
        return redirect('admin:index')


admin.site.register(RegistrationSettings, RegistrationSettingsAdmin)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'full_name', 'group', 'is_approved', 'get_is_staff', 'get_is_superuser', 'date_joined']
    list_filter = ['is_approved', 'is_staff', 'is_superuser']
    search_fields = ['username', 'full_name', 'group']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личная информация', {'fields': ('full_name', 'group')}),
        ('Статус', {'fields': ('is_approved', 'is_active', 'is_staff', 'is_superuser')}),
        ('Права доступа', {'fields': ('groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    def get_is_staff(self, obj):
        return obj.is_staff
    get_is_staff.short_description = 'Администратор'
    get_is_staff.boolean = True

    def get_is_superuser(self, obj):
        return obj.is_superuser
    get_is_superuser.short_description = 'Суперпользователь'
    get_is_superuser.boolean = True

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Меняем labels для полей в форме
        if 'is_staff' in form.base_fields:
            form.base_fields['is_staff'].label = 'Администратор'
        if 'is_superuser' in form.base_fields:
            form.base_fields['is_superuser'].label = 'Суперпользователь'
        return form


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
