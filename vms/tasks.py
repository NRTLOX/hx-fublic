from celery import shared_task
from django.utils import timezone
from .models import UserVMInstance
from .proxmox_client import proxmox_client
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def cleanup_expired_vms(self):
    """
    Автоматически уничтожает все просроченные VM.
    Запускается по расписанию Celery Beat.
    """
    expired_vms = UserVMInstance.objects.filter(
        status='running',
        expires_at__lt=timezone.now()
    ).select_related('user', 'task')

    destroyed_count = 0

    for vm in expired_vms:
        try:
            if vm.proxmox_vm_id:
                try:
                    proxmox_client.stop_vm(vm.proxmox_vm_id)
                except Exception:
                    pass  # уже может быть остановлена

                try:
                    proxmox_client.destroy_vm(vm.proxmox_vm_id)
                except Exception:
                    pass

            vm.status = 'destroyed'
            vm.save(update_fields=['status', 'updated_at'])

            destroyed_count += 1
            logger.info(
                f"[AUTO-CLEANUP] Уничтожена просроченная VM "
                f"{vm.proxmox_vm_id} пользователя {vm.user.username} "
                f"(задание: {vm.task.title})"
            )

        except Exception as exc:
            logger.error(f"[AUTO-CLEANUP] Ошибка при очистке VM {vm.id}: {exc}")
            # можно сделать retry при необходимости

    if destroyed_count > 0:
        logger.info(f"[AUTO-CLEANUP] Всего уничтожено просроченных VM: {destroyed_count}")

    return destroyed_count
