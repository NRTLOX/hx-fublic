from django.contrib import admin
from .models import UserVMInstance

@admin.register(UserVMInstance)
class UserVMInstanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'task', 'ip_address', 'status', 'started_at', 'expires_at']
    list_filter = ['status', 'task']
    search_fields = ['user__username', 'ip_address', 'task__title']
    readonly_fields = ['proxmox_vm_id', 'started_at', 'expires_at']
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['monitoring_link'] = get_monitoring_link()
        return super().changelist_view(request, extra_context=extra_context)

from django.urls import reverse
from django.utils.html import format_html

def get_monitoring_link():
    url = reverse('admin_monitoring')
    return format_html('<a href="{}" class="btn btn-primary" style="margin-bottom:10px;">📊 Мониторинг системы</a>', url)
