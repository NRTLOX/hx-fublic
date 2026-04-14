from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import time
from tasks.models import Task
from .models import UserVMInstance
from .proxmox_client import proxmox_client


def get_next_free_ip():
    """Находит следующий свободный IP начиная с 10.100.50.101"""
    used_ips = UserVMInstance.objects.filter(status='running').values_list('ip_address', flat=True)

    base_ip = "10.100.50."
    for i in range(101, 250):
        ip = f"{base_ip}{i}"
        if ip not in used_ips:
            return ip
    return None


def generate_vm_id(user, task):
    """
    Генерирует уникальный ID для VM в формате: 8 + ID пользователя + ID задания
    Пример: пользователь 7, задание 12 → 8712
    """
    vm_id_str = f"8{user.id}{task.id}"
    return int(vm_id_str)

@login_required
def start_vm(request, task_id):
    task = get_object_or_404(Task, id=task_id, task_type='vm', is_active=True)

    # Удаляем старые записи, если есть
    UserVMInstance.objects.filter(user=request.user, task=task).delete()

    ip_address = get_next_free_ip()
    if not ip_address:
        messages.error(request, "Все IP-адреса заняты.")
        return redirect('task_detail', task_id=task.id)

    new_vm_id = generate_vm_id(request.user, task)

    try:
        # Клонируем шаблон (без сообщений пользователю)
        proxmox_client.clone_vm(task.proxmox_template_id, new_vm_id)

        # Устанавливаем IP
        proxmox_client.set_ip(new_vm_id, ip_address)

        # Запускаем машину
        proxmox_client.start_vm(new_vm_id)

        # Сохраняем в базу
        vm_instance = UserVMInstance.objects.create(
            user=request.user,
            task=task,
            proxmox_vm_id=new_vm_id,
            ip_address=ip_address,
            status='running',
            started_at=timezone.now(),
            expires_at=timezone.now() + timedelta(hours=1)
        )

        # Только финальное сообщение
        messages.success(request, f"✅ Виртуальная машина успешно запущена! IP: {ip_address}")

    except Exception as e:
        print(f"[ERROR] start_vm: {str(e)}")
        messages.error(request, "Не удалось запустить виртуальную машину. Обратитесь к администратору.")
        # Попытка очистки
        try:
            proxmox_client.destroy_vm(new_vm_id)
        except:
            pass

    return redirect('task_detail', task_id=task.id)



@login_required
def stop_vm(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    vm_instance = UserVMInstance.objects.filter(user=request.user, task=task).first()

    if not vm_instance or vm_instance.status != 'running':
        messages.warning(request, "Машина не запущена.")
        return redirect('task_detail', task_id=task.id)

    try:
        if vm_instance.proxmox_vm_id:
            proxmox_client.stop_vm(vm_instance.proxmox_vm_id)
            time.sleep(8)
            proxmox_client.destroy_vm(vm_instance.proxmox_vm_id)

        vm_instance.status = 'destroyed'
        vm_instance.save()

        messages.success(request, "✅ Виртуальная машина успешно остановлена и удалена.")

    except Exception as e:
        print(f"[ERROR] stop_vm: {str(e)}")
        messages.error(request, "Не удалось остановить виртуальную машину. Обратитесь к администратору.")

    return redirect('task_detail', task_id=task.id)



@login_required
def reset_timer(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    vm_instance = UserVMInstance.objects.filter(user=request.user, task=task, status='running').first()

    if vm_instance:
        vm_instance.expires_at = timezone.now() + timedelta(hours=1)
        vm_instance.save()
        messages.success(request, "Таймер продлён на 1 час.")
    else:
        messages.warning(request, "Машина не запущена.")

    return redirect('task_detail', task_id=task.id)
