from django.contrib import admin
from .models import Task, Flag, Submission

class FlagInline(admin.TabularInline):
    model = Flag
    extra = 1
    fields = ['flag_value', 'hint', 'description']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'task_type', 'points', 'is_active', 'created_at']
    list_filter = ['task_type', 'is_active']
    search_fields = ['title', 'description']
    inlines = [FlagInline]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'task', 'submitted_flag', 'is_correct', 'submitted_at']
    list_filter = ['is_correct', 'task']
    search_fields = ['user__username', 'submitted_flag']
