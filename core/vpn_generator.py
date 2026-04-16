import os
import subprocess
from django.conf import settings
from .models import VPNClient, UserNetwork

class VPNGenerator:
    EASY_RSA_PATH = "/etc/easy-rsa"
    OPENVPN_CCD_PATH = "/etc/openvpn/ccd"

    @staticmethod
    def get_or_create_network(user):
        """Выделяет пользователю уникальную подсеть 10.100.51.0/24 и дальше"""
        network, created = UserNetwork.objects.get_or_create(user=user)
        
        if created:
            # Находим следующую свободную подсеть начиная с 51
            used_subnets = UserNetwork.objects.values_list('subnet', flat=True)
            base = 51
            while True:
                subnet = f"10.100.{base}.0/24"
                if subnet not in used_subnets:
                    network.subnet = subnet
                    network.save()
                    print(f"[VPN] Пользователю {user.username} назначена подсеть {subnet}")
                    break
                base += 1
                if base > 200:  # защита от переполнения
                    raise Exception("Не удалось найти свободную подсеть")
        
        return network

    @staticmethod
    def get_or_create_client(user):
        """Создаёт клиентский сертификат"""
        client, created = VPNClient.objects.get_or_create(
            user=user,
            defaults={'certificate_name': f"client_{user.username}"}
        )

        if created:
            cert_name = client.certificate_name
            try:
                subprocess.run([
                    os.path.join(VPNGenerator.EASY_RSA_PATH, "easyrsa"),
                    "--batch",
                    "build-client-full",
                    cert_name,
                    "nopass"
                ], cwd=VPNGenerator.EASY_RSA_PATH, check=True, capture_output=True)
                print(f"[VPN] Сертификат для {user.username} создан")
            except Exception as e:
                print(f"[VPN] Ошибка создания сертификата: {e}")
                return None

        return client

    @staticmethod
    def generate_ovpn_config(user):
        """Генерирует полный .ovpn конфиг с индивидуальным маршрутом"""
        client = VPNGenerator.get_or_create_client(user)
        if not client:
            return None

        network = VPNGenerator.get_or_create_network(user)
        cert_name = client.certificate_name

        try:
            # Создаём CCD файл (client-config-dir)
            ccd_dir = VPNGenerator.OPENVPN_CCD_PATH
            os.makedirs(ccd_dir, exist_ok=True)
            
            ccd_content = f'push "route {network.subnet.split("/")[0]} 255.255.255.0"\n'
            with open(os.path.join(ccd_dir, cert_name), 'w') as f:
                f.write(ccd_content)

            # Читаем сертификаты
            ca = open('/etc/openvpn/ca.crt').read()
            cert = open(f'/etc/easy-rsa/pki/issued/{cert_name}.crt').read()
            key = open(f'/etc/easy-rsa/pki/private/{cert_name}.key').read()

            config = f"""client
dev tun
proto udp
remote 10.4.50.15 1194
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
cipher AES-256-GCM
auth SHA512
verb 3

<ca>
{ca}</ca>
<cert>
{cert}</cert>
<key>
{key}</key>
"""

            return config

        except Exception as e:
            print(f"[VPN] Ошибка при генерации конфига: {e}")
            return None
