from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, VPNClient, UserNetwork

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
