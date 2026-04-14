import os
import subprocess
from django.conf import settings
from .models import VPNClient

class VPNGenerator:
    EASY_RSA_PATH = "/etc/easy-rsa"
    OPENVPN_PATH = "/etc/openvpn"

    @staticmethod
    def get_or_create_client(user):
        """Создаёт или возвращает клиентский сертификат"""
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

                print(f"[VPN] Сертификат для пользователя {user.username} создан")
            except subprocess.CalledProcessError as e:
                print(f"[VPN] Ошибка создания сертификата: {e.stderr.decode()}")
                return None

        return client

    @staticmethod
    def generate_ovpn_config(user):
        """Генерирует полный .ovpn файл"""
        client = VPNGenerator.get_or_create_client(user)
        if not client:
            return None

        cert_name = client.certificate_name

        # Замени ТВОЙ_ВНЕШНИЙ_IP на реальный внешний IP твоего Proxmox
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
{open('/etc/openvpn/ca.crt').read()}
</ca>
<cert>
{open(f'/etc/easy-rsa/pki/issued/{cert_name}.crt').read()}
</cert>
<key>
{open(f'/etc/easy-rsa/pki/private/{cert_name}.key').read()}
</key>
"""

        return config
