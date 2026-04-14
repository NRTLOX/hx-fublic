from django.contrib import admin
from .models import UserVMInstance

@admin.register(UserVMInstance)
class UserVMInstanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'task', 'ip_address', 'status', 'started_at', 'expires_at']
    list_filter = ['status', 'task']
    search_fields = ['user__username', 'ip_address', 'task__title']
    readonly_fields = ['proxmox_vm_id', 'started_at', 'expires_at']
