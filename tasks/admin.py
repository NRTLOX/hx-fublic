from django.contrib import admin
from django.db import models
from .models import Task, Flag, Submission


class FlagInline(admin.TabularInline):
    model = Flag
    extra = 1
    fields = ['label', 'flag_value', 'hint', 'description', 'file_path']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'task_type', 'points', 'is_active', 'get_allowed_groups', 'created_at']
    list_filter = ['task_type', 'is_active', 'allowed_groups']
    search_fields = ['title', 'description']
    inlines = [FlagInline]
    filter_horizontal = ['allowed_groups']

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
        ('Доступ', {
            'fields': ('allowed_groups',),
            'description': 'Если не выбрать ни одной группы — задание видно всем одобренным участникам.'
        }),
    )

    # Убираем старый formfield_overrides для readme (больше не нужен)

    def get_allowed_groups(self, obj):
        groups = list(obj.allowed_groups.all())
        return ', '.join(g.name for g in groups) if groups else 'Все'
    get_allowed_groups.short_description = 'Доступ'


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'task', 'submitted_flag', 'is_correct', 'submitted_at']
    list_filter = ['is_correct', 'task']
    search_fields = ['user__username', 'submitted_flag']
