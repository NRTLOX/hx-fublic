import subprocess
import os

def test_generate_for_user(username):
    print(f"\n=== ТЕСТ ГЕНЕРАЦИИ ДЛЯ ПОЛЬЗОВАТЕЛЯ {username} ===")
    
    client_name = f"client_{username}"
    
    try:
        # 1. Создаём клиентский сертификат
        print(f"Создаём сертификат {client_name}...")
        result = subprocess.run([
            "docker", "exec", "openvpn",
            "easyrsa", "--batch", "build-client-full", client_name, "nopass"
        ], capture_output=True, text=True)

        print("Вывод easyrsa:", result.stdout)
        if result.returncode != 0:
            print("Ошибка easyrsa:", result.stderr)

        # 2. Получаем ovpn конфиг
        print("Получаем ovpn_getclient...")
        result = subprocess.run([
            "docker", "exec", "openvpn",
            "ovpn_getclient", client_name
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Конфиг успешно получен! Первые 30 строк:")
            print(result.stdout[:1000])
            
            # Сохраняем в файл
            with open(f"/root/{username}_test.ovpn", "w") as f:
                f.write(result.stdout)
            print(f"Файл сохранён: /root/{username}_test.ovpn")
        else:
            print("Ошибка ovpn_getclient:", result.stderr)

    except Exception as e:
        print(f"Общая ошибка: {e}")

if __name__ == "__main__":
    test_generate_for_user("www")   # замени на нужного пользователя
