from django.contrib import admin
from django.db import models
from .models import Task, Flag, Submission


class FlagInline(admin.TabularInline):
    model = Flag
    extra = 1
    fields = ['flag_value', 'hint', 'description', 'file_path']   # добавили file_path


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'task_type', 'points', 'is_active', 'created_at']
    list_filter = ['task_type', 'is_active']
    search_fields = ['title', 'description']
    inlines = [FlagInline]

    # Делаем поле README большим и удобным
    fieldsets = (
        (None, {
            'fields': ('title', 'task_type', 'points', 'is_active')
        }),
        ('Описание', {
            'fields': ('description', 'readme'),
            'description': 'Краткое описание + полное README в формате Markdown'
        }),
        ('Файлы и Proxmox', {
            'fields': ('file', 'proxmox_template_id')
        }),
    )
   
    formfield_overrides = {
        models.TextField: {'widget': admin.widgets.AdminTextareaWidget(attrs={'rows': 20})},
    }


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'task', 'submitted_flag', 'is_correct', 'submitted_at']
    list_filter = ['is_correct', 'task']
    search_fields = ['user__username', 'submitted_flag']
