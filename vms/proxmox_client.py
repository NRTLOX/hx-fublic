from proxmoxer import ProxmoxAPI
from django.conf import settings
import time

class ProxmoxClient:
    def __init__(self):
        self.proxmox = ProxmoxAPI(
            host=settings.PROXMOX_HOST,
            user="root@pam",
            token_name="ctf-platform",
            token_value=settings.PROXMOX_TOKEN_SECRET,
            verify_ssl=False,
            port=8006
        )
        self.node = settings.PROXMOX_NODE
        print(f"[Proxmox] Client initialized for node: {self.node}")

    def clone_vm(self, template_id, new_vm_id, name=None):
        print(f"[Proxmox] → Клонируем шаблон {template_id} → VM {new_vm_id}")
        
        task = self.proxmox.nodes(self.node).qemu(template_id).clone.post(
            newid=new_vm_id,
            name=name or f"ctf-vm-{new_vm_id}",
            full=1,
            target=self.node
        )
        
        print(f"[Proxmox] Задача клонирования: {task}")
        success = self.wait_for_task(task, timeout=90)
        if not success:
            raise Exception("Клонирование не завершилось успешно")
        
        time.sleep(8)
        return True

    def set_ip(self, vm_id, ip_address):
        print(f"[Proxmox] → Устанавливаем IP {ip_address} для VM {vm_id}")
        return self.proxmox.nodes(self.node).qemu(vm_id).config.put(
            ipconfig0=f"ip={ip_address}/24,gw=10.100.50.1"
        )

    def start_vm(self, vm_id):
        print(f"[Proxmox] → Запускаем VM {vm_id}")
        time.sleep(15)
        return self.proxmox.nodes(self.node).qemu(vm_id).status.start.post()

    def stop_vm(self, vm_id):
        print(f"[Proxmox] → Останавливаем VM {vm_id}")
        return self.proxmox.nodes(self.node).qemu(vm_id).status.shutdown.post()

    def destroy_vm(self, vm_id):
        """Полностью удаляем VM + конфиг"""
        print(f"[Proxmox] → Уничтожаем VM {vm_id}")
        try:
            # Основное удаление
            self.proxmox.nodes(self.node).qemu(vm_id).delete(purge=1)
            print(f"[Proxmox] Удаление VM {vm_id} запущено")
            time.sleep(5)
            
            # Принудительно удаляем конфиг файл, если он остался
            try:
                import subprocess
                subprocess.run(['rm', '-f', f'/etc/pve/qemu-server/{vm_id}.conf'], 
                             check=False, timeout=10)
                print(f"[Proxmox] Конфиг файл {vm_id}.conf удалён")
            except:
                pass
                
        except Exception as e:
            print(f"[Proxmox] Ошибка при destroy: {e}")
            # Последняя попытка через shell
            try:
                import subprocess
                subprocess.run(['qm', 'destroy', str(vm_id), '--purge'], 
                             check=False, timeout=15)
                print(f"[Proxmox] qm destroy --purge выполнен")
            except:
                pass

    def wait_for_task(self, task_id, timeout=90):
        print(f"[Proxmox] Ожидаем задачу {task_id}...")
        start = time.time()
        while time.time() - start < timeout:
            try:
                status = self.proxmox.nodes(self.node).tasks(task_id).status.get()
                print(f"[Proxmox] Статус: {status.get('status')} | exit: {status.get('exitstatus')}")
                if status.get('status') == 'stopped':
                    return status.get('exitstatus') == 'OK'
            except:
                pass
            time.sleep(4)
        print(f"[Proxmox] Таймаут задачи {task_id}")
        return False


proxmox_client = ProxmoxClient()
