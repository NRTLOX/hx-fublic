from django.core.management.base import BaseCommand
from django.utils import timezone
from vms.models import UserVMInstance
import time


class Command(BaseCommand):
    help = 'Автоматически уничтожает просроченные виртуальные машины по таймеру'

    def handle(self, *args, **options):
        from vms.proxmox_client import proxmox_client

        expired_vms = UserVMInstance.objects.filter(
            status='running',
            expires_at__lt=timezone.now()
        ).select_related('user', 'task')

        count = 0

        for vm in expired_vms:
            try:
                if vm.proxmox_vm_id:
                    self.stdout.write(
                        f"→ Останавливаем VM {vm.proxmox_vm_id} "
                        f"(пользователь: {vm.user.username})..."
                    )
                    proxmox_client.stop_vm(vm.proxmox_vm_id)

                    self.stdout.write("   Ждём 10 секунд...")
                    time.sleep(10)

                    self.stdout.write(f"→ Уничтожаем VM {vm.proxmox_vm_id}...")
                    proxmox_client.destroy_vm(vm.proxmox_vm_id)

                # Удаляем запись, а не помечаем destroyed — иначе её ip_address
                # (уникален глобально) навсегда блокирует повторное использование
                # этого IP, даже для другого пользователя с той же подсетью.
                vm.delete()

                count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Уничтожена VM {vm.proxmox_vm_id}")
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Ошибка при очистке VM {vm.proxmox_vm_id}: {e}")
                )

        if count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\nВсего уничтожено просроченных VM: {count}")
            )
        else:
            self.stdout.write("Просроченных VM не найдено.")
