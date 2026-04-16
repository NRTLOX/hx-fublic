import os
import subprocess
from .models import VPNClient, UserNetwork

class VPNGenerator:

    @staticmethod
    def get_or_create_network(user):
        network, created = UserNetwork.objects.get_or_create(user=user)
        
        if created or not network.subnet:
            used = set(UserNetwork.objects.exclude(user=user).values_list('subnet', flat=True))
            base = 51
            while True:
                subnet = f"10.100.{base}.0/24"
                if subnet not in used:
                    network.subnet = subnet
                    network.save()
                    print(f"[VPN] Пользователю {user.username} назначена подсеть {subnet}")
                    break
                base += 1
                if base > 200:
                    raise Exception("Не удалось найти свободную подсеть")
        
        return network

    @staticmethod
    def generate_ovpn_config(user):
        print(f"[VPN] generate_ovpn_config вызвана для {user.username}")

        try:
            cert_name = f"client_{user.username}"

            # 1. Назначаем подсеть
            network = VPNGenerator.get_or_create_network(user)
            print(f"[VPN] Подсеть: {network.subnet}")

            # 2. Отзываем старый сертификат (если был) и создаём новый
            print(f"[VPN] Пересоздаём сертификат {cert_name}...")
            subprocess.run([
                "docker", "exec", "openvpn",
                "easyrsa", "--batch", "revoke", cert_name
            ], check=False)  # ignore error if not exists

            # Создаём новый сертификат
            subprocess.run([
                "docker", "exec", "openvpn",
                "easyrsa", "--batch", "build-client-full", cert_name, "nopass"
            ], check=True, capture_output=True)
            print(f"[VPN] Сертификат {cert_name} создан")

            # 3. Создаём CCD файл
            ccd_dir = "/var/www/hxctf/openvpn-data/ccd"
            os.makedirs(ccd_dir, exist_ok=True)
            ccd_file = os.path.join(ccd_dir, cert_name)
            
            with open(ccd_file, 'w') as f:
                f.write(f'push "route {network.subnet.split("/")[0]} 255.255.255.0"\n')
            
            print(f"[VPN] CCD файл создан: {ccd_file}")

            # 4. Получаем конфиг
            result = subprocess.run([
                "docker", "exec", "openvpn",
                "ovpn_getclient", cert_name
            ], capture_output=True, text=True, check=True)

            print(f"[VPN] УСПЕХ: Конфиг сгенерирован для {user.username}")
            return result.stdout

        except subprocess.CalledProcessError as e:
            print(f"[VPN] Ошибка docker команды: {e}")
            return None
        except Exception as e:
            print(f"[VPN] Неожиданная ошибка: {e}")
            return None
