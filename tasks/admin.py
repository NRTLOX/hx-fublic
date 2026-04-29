from django.contrib import admin
from django.db import models
from .models import Task, Flag, Submission


class FlagInline(admin.TabularInline):
    model = Flag
    extra = 1
    fields = ['flag_value', 'hint', 'description', 'file_path']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'task_type', 'points', 'is_active', 'created_at']
    list_filter = ['task_type', 'is_active']
    search_fields = ['title', 'description']
    inlines = [FlagInline]

    fieldsets = (
        (None, {
            'fields': ('title', 'task_type', 'points', 'is_active')
        }),
        ('Описание', {
            'fields': ('description', 'readme_file'),   # ← теперь файл, а не textarea
            'description': 'Краткое описание + файл README (HTML или PDF)'
        }),
        ('Файлы и Proxmox', {
            'fields': ('file', 'proxmox_template_id')
        }),
    )

    # Убираем старый formfield_overrides для readme (больше не нужен)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'task', 'submitted_flag', 'is_correct', 'submitted_at']
    list_filter = ['is_correct', 'task']
    search_fields = ['user__username', 'submitted_flag']
