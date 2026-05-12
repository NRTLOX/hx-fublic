from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import time
from tasks.models import Task
from .models import UserVMInstance
from .proxmox_client import proxmox_client
import random
import string


def get_next_free_ip(user):
    """Находит следующий свободный IP в личной подсети пользователя"""
    from core.models import UserNetwork
    
    try:
        user_network = UserNetwork.objects.get(user=user)
        third_octet = user_network.subnet.split('.')[2]
    except UserNetwork.DoesNotExist:
        print(f"[VM] У пользователя {user.username} ещё не назначена подсеть")
        return None
    except Exception as e:
        print(f"[VM] Ошибка получения подсети пользователя {user.username}: {e}")
        return None

    base_ip = f"10.100.{third_octet}."
    
    used_ips = UserVMInstance.objects.filter(
        status__in=['running', 'stopped']
    ).values_list('ip_address', flat=True)

    for i in range(101, 250):
        ip = f"{base_ip}{i}"
        if ip not in used_ips:
            return ip

    print(f"[VM] В подсети {base_ip}0/24 все IP заняты")
    return None


def generate_vm_id(user, task):
    """
    Генерирует уникальный ID для VM в формате: 8 + ID пользователя + ID задания
    Пример: пользователь 7, задание 12 → 8712
    """
    vm_id_str = f"8{user.id}00{task.id}"
    return int(vm_id_str)




@login_required
def start_vm(request, task_id):
    task = get_object_or_404(Task, id=task_id, task_type='vm', is_active=True)

    # Удаляем старую запись VM для этого пользователя и задания
    UserVMInstance.objects.filter(user=request.user, task=task).delete()

    ip_address = get_next_free_ip(request.user)
    if not ip_address:
        messages.error(request, "Все IP-адреса в твоей подсети заняты.")
        return redirect('task_detail', task_id=task.id)

    new_vm_id = generate_vm_id(request.user, task)

    try:
        # 1. Клонируем шаблон
        proxmox_client.clone_vm(task.proxmox_template_id, new_vm_id)

        # 2. Устанавливаем IP
        proxmox_client.set_ip(new_vm_id, ip_address)

        # 3. Запускаем машину
        proxmox_client.start_vm(new_vm_id)

        # 4. Сохраняем VM в базу
        vm_instance = UserVMInstance.objects.create(
            user=request.user,
            task=task,
            proxmox_vm_id=new_vm_id,
            ip_address=ip_address,
            status='running',
            started_at=timezone.now(),
            expires_at=timezone.now() + timedelta(minutes=60),
            generated_flags={}   # инициализируем пустой словарь
        )

        # === 5. Генерация уникальных флагов и вставка в файлы ===
        inserted_count = 0
        generated_flags_dict = {}

        time.sleep(20)  # ждём запуска Guest Agent

        for flag_obj in task.flags.all():
            if flag_obj.file_path:
                # Генерируем уникальный флаг для этого студента
                random_part = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
                unique_flag = f"flag{{{random_part}}}"

                try:
                    command = f"echo '{unique_flag}' > {flag_obj.file_path}"
                    success = proxmox_client.exec_command(new_vm_id, command)
                    
                    if success:
                        inserted_count += 1
                        generated_flags_dict[str(flag_obj.id)] = unique_flag
                        print(f"[VM] Флаг вставлен в {flag_obj.file_path} для {request.user.username}")
                    else:
                        print(f"[VM] Не удалось вставить флаг в {flag_obj.file_path}")
                except Exception as e:
                    print(f"[VM] Ошибка вставки флага: {e}")

        # Сохраняем сгенерированные флаги в VMInstance
        vm_instance.generated_flags = generated_flags_dict
        vm_instance.save()

        # Финальное сообщение
        success_msg = f"Виртуальная машина успешно запущена! IP: {ip_address}"
        if inserted_count > 0:
            success_msg += f" | Вставлено флагов: {inserted_count}"

        messages.success(request, success_msg)

    except Exception as e:
        print(f"[ERROR] start_vm: {str(e)}")
        messages.error(request, "Не удалось запустить виртуальную машину. Обратитесь к администратору.")

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

        messages.success(request, "Виртуальная машина успешно остановлена и удалена.")

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
