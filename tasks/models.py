from django.db import models
from django.conf import settings
import markdown
import random
import string

class Task(models.Model):
    TYPE_CHOICES = [
        ('file', 'Файл на взлом'),
        ('vm', 'Виртуальная машина'),
    ]

    title = models.CharField(max_length=200, verbose_name="Название задания")
    description = models.TextField(verbose_name="Краткое описание", blank=True)
   
    # Новое большое поле README в Markdown
    readme = models.TextField(
        blank=True,
        null=True,
        verbose_name="README (Markdown)",
        help_text="Полное описание задания с форматированием. Поддерживает Markdown, картинки, код и т.д."
    )
   
    task_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='file', verbose_name="Тип задания")
   
    # Для файловых заданий
    file = models.FileField(upload_to='tasks/files/', blank=True, null=True, verbose_name="Файл для скачивания")
   
    # Для VM заданий
    proxmox_template_id = models.IntegerField(blank=True, null=True, verbose_name="ID шаблона в Proxmox")
   
    points = models.PositiveIntegerField(default=100, verbose_name="Баллы")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Задание"
        verbose_name_plural = "Задания"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_task_type_display()})"

    def get_readme_html(self):
        """Преобразует Markdown в безопасный HTML"""
        if not self.readme:
            return ''
        return markdown.markdown(
            self.readme,
            extensions=['fenced_code', 'tables', 'nl2br', 'attr_list']
        )

class Flag(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='flags')
    
    # Поле можно оставлять пустым — флаг будет генерироваться автоматически при запуске VM
    flag_value = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name="Флаг (оставь пустым — будет генерироваться автоматически)"
    )
    
    hint = models.CharField(max_length=300, blank=True, verbose_name="Подсказка (где искать флаг)")
    description = models.CharField(max_length=200, blank=True, verbose_name="Описание для админа")
    
    # Путь, куда вставлять флаг внутри VM
    file_path = models.CharField(
        max_length=300, 
        blank=True, 
        null=True, 
        verbose_name="Путь к файлу в VM (для авто-вставки)"
    )

    class Meta:
        verbose_name = "Флаг"
        verbose_name_plural = "Флаги"

    def __str__(self):
        return f"Флаг для {self.task.title}"


class Submission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name="Задание")
    flag = models.ForeignKey(Flag, on_delete=models.SET_NULL, null=True, blank=True)
    submitted_flag = models.CharField(max_length=255, verbose_name="Отправленный флаг")
    is_correct = models.BooleanField(default=False, verbose_name="Правильно")
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Сабмит"
        verbose_name_plural = "Сабмиты"
        ordering = ['-submitted_at']
        unique_together = ('user', 'flag')

    def __str__(self):
        return f"{self.user.username} -> {self.task.title} ({'✅' if self.is_correct else '❌'})"
