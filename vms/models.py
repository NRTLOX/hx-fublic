from django.db import models
from django.conf import settings
from tasks.models import Task
from django.utils import timezone

class UserVMInstance(models.Model):
    STATUS_CHOICES = [
        ('running', 'Запущена'),
        ('stopped', 'Остановлена'),
        ('destroyed', 'Уничтожена'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name="Задание")
    
    proxmox_vm_id = models.IntegerField(null=True, blank=True, verbose_name="ID VM в Proxmox")
    ip_address = models.GenericIPAddressField(protocol='ipv4', unique=True, verbose_name="IP-адрес")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='stopped', verbose_name="Статус")
    
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Время запуска")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Время окончания")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Запущенная VM пользователя"
        verbose_name_plural = "Запущенные VM пользователей"
        unique_together = ('user', 'task')  # Один пользователь — одна VM на задание

    def __str__(self):
        return f"{self.user.username} — {self.task.title} ({self.ip_address})"

    @property
    def is_expired(self):
        if self.expires_at and self.status == 'running':
            return timezone.now() > self.expires_at
        return False

    def get_remaining_time(self):
        if self.expires_at and self.status == 'running':
            remaining = self.expires_at - timezone.now()
            if remaining.total_seconds() > 0:
                minutes = int(remaining.total_seconds() // 60)
                seconds = int(remaining.total_seconds() % 60)
                return f"{minutes:02d}:{seconds:02d}"
        return "00:00"

class VMFlag(models.Model):
    vm_instance = models.ForeignKey('vms.UserVMInstance', on_delete=models.CASCADE, related_name='flags')
    flag_obj = models.ForeignKey('tasks.Flag', on_delete=models.CASCADE)  # ссылка на шаблон флага
    generated_flag = models.CharField(max_length=255, verbose_name="Сгенерированный флаг")
    file_path = models.CharField(max_length=300, verbose_name="Путь, куда вставлен флаг")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Флаг в VM"
        verbose_name_plural = "Флаги в VM"
        unique_together = ('vm_instance', 'flag_obj')

    def __str__(self):
        return f"{self.generated_flag} → {self.file_path}"
