from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import User, VPNClient, UserNetwork, RegistrationSettings, GroupRegistrationSettings


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
    list_display = ['username', 'full_name', 'group', 'get_groups', 'is_approved', 'get_is_staff', 'get_is_superuser', 'date_joined']
    list_filter = ['is_approved', 'is_staff', 'is_superuser', 'groups']
    search_fields = ['username', 'full_name', 'group']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личная информация', {'fields': ('full_name', 'group')}),
        ('Статус', {'fields': ('is_approved', 'is_active', 'is_staff', 'is_superuser')}),
        ('Группы и доступ к заданиям', {
            'fields': ('groups', 'user_permissions'),
            'description': 'Группы отсюда используются, в том числе, для ограничения доступа к заданиям '
                            '(настраивается в самом задании, поле «Доступно только группам»). '
                            'Создать новую группу можно на странице Группы.'
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    def get_groups(self, obj):
        return ', '.join(g.name for g in obj.groups.all()) or '—'
    get_groups.short_description = 'Группы доступа'

    def get_is_staff(self, obj):
        return obj.is_staff
    get_is_staff.short_description = 'Администратор'
    get_is_staff.boolean = True
    get_is_staff.admin_order_field = 'is_staff'

    def get_is_superuser(self, obj):
        return obj.is_superuser
    get_is_superuser.short_description = 'Суперпользователь'
    get_is_superuser.boolean = True
    get_is_superuser.admin_order_field = 'is_superuser'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Меняем labels для полей в форме
        if 'is_staff' in form.base_fields:
            form.base_fields['is_staff'].label = 'Администратор'
        if 'is_superuser' in form.base_fields:
            form.base_fields['is_superuser'].label = 'Суперпользователь'
        return form


class GroupRegistrationSettingsInline(admin.StackedInline):
    model = GroupRegistrationSettings
    can_delete = False
    verbose_name = "Настройка регистрации"
    verbose_name_plural = "Настройка регистрации"


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin):
    inlines = [GroupRegistrationSettingsInline]
    list_display = ['name', 'get_registration_open']

    def get_registration_open(self, obj):
        settings_obj = getattr(obj, 'registration_settings', None)
        return settings_obj.is_open_for_registration if settings_obj else True
    get_registration_open.short_description = 'Доступна при регистрации'
    get_registration_open.boolean = True


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
