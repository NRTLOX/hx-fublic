# HX CTF Platform

Платформа для проведения соревнований по информационной безопасности (Capture The Flag) с поддержкой виртуальных машин на базе Proxmox.

## Описание

HX CTF Platform — это веб-приложение на Django для организации CTF-соревнований. Платформа позволяет:

- Создавать задания двух типов: файловые и с виртуальными машинами
- Автоматически разворачивать изолированные VM для каждого участника
- Генерировать уникальные флаги для каждого студента
- Управлять доступом через VPN с индивидуальными подсетями
- Отслеживать прогресс участников и вести таблицу лидеров

## Основные возможности

### Для участников
- Регистрация с модерацией администратором
- Скачивание персонального VPN-конфига для доступа к инфраструктуре
- Просмотр списка заданий и их описаний
- Запуск персональных виртуальных машин (автоматическое клонирование из шаблона)
- Отправка флагов и получение баллов
- Просмотр таблицы лидеров и личной статистики

### Для администраторов
- Управление регистрацией (открытие/закрытие, временные окна)
- Создание заданий с поддержкой HTML/PDF описаний
- Настройка шаблонов VM в Proxmox
- Автоматическая генерация уникальных флагов для каждого участника
- Мониторинг запущенных виртуальных машин
- Автоматическое удаление просроченных VM

## Технологический стек

- **Backend**: Django 6.0.4, Python 3.x
- **Database**: SQLite (можно заменить на PostgreSQL)
- **Task Queue**: Celery + Redis
- **Virtualization**: Proxmox VE (через API)
- **VPN**: OpenVPN (в Docker-контейнере)
- **Static Files**: WhiteNoise
- **Frontend**: HTML, CSS, Bootstrap (через шаблоны Django)

## Архитектура

### Структура проекта

```
hx-fublic/
├── core/                   # Основное приложение (аутентификация, профили, VPN)
│   ├── models.py          # User, RegistrationSettings, VPNClient, UserNetwork
│   ├── views.py           # Регистрация, логин, профиль, лидерборд
│   ├── vpn_generator.py   # Генерация VPN-конфигов
│   └── forms.py           # Формы регистрации и входа
├── tasks/                  # Приложение для заданий
│   ├── models.py          # Task, Flag, Submission
│   ├── views.py           # Список заданий, детали, отправка флагов
│   └── urls.py
├── vms/                    # Приложение для управления VM
│   ├── models.py          # UserVMInstance
│   ├── views.py           # Запуск, остановка, продление VM
│   ├── proxmox_client.py  # Клиент для работы с Proxmox API
│   ├── tasks.py           # Celery-задачи для очистки VM
│   └── management/commands/cleanup_expired_vms.py
├── hxctf/                  # Настройки проекта
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── templates/              # HTML-шаблоны
├── static/                 # Статические файлы
├── media/                  # Загружаемые файлы (задания, README)
├── openvpn-data/          # Данные OpenVPN
├── requirements.txt
└── manage.py
```

### Модели данных

#### User (core/models.py)
- Расширенная модель пользователя Django
- Поля: `is_approved`, `full_name`, `group`
- Связи: `vpn_client`, `network`

#### Task (tasks/models.py)
- Задания CTF
- Типы: `file` (файл для скачивания), `vm` (виртуальная машина)
- Поля: `title`, `description`, `readme_file`, `file`, `proxmox_template_id`, `points`

#### Flag (tasks/models.py)
- Флаги для заданий
- Поля: `flag_value`, `hint`, `file_path` (для автоматической вставки в VM)

#### UserVMInstance (vms/models.py)
- Запущенные виртуальные машины пользователей
- Поля: `proxmox_vm_id`, `ip_address`, `status`, `expires_at`, `generated_flags`

#### UserNetwork (core/models.py)
- Персональные подсети пользователей
- Формат: `10.100.X.0/24` (где X — уникальный номер)

## Установка и настройка

### Требования

- Python 3.8+
- Proxmox VE сервер с настроенным API
- Docker (для OpenVPN)
- Redis (для Celery)

### Шаги установки

1. **Клонирование репозитория**
```bash
git clone <repository-url>
cd hx-fublic
```

2. **Создание виртуального окружения**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. **Установка зависимостей**
```bash
pip install -r requirements.txt
```

4. **Настройка переменных окружения**

Создайте файл `.env` в корне проекта:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True

# Proxmox настройки
PROXMOX_HOST=10.100.0.254
PROXMOX_NODE=pve
PROXMOX_TOKEN_ID=ctf-platform
PROXMOX_TOKEN_SECRET=your-proxmox-token-secret
```

5. **Применение миграций**
```bash
python manage.py migrate
```

6. **Создание суперпользователя**
```bash
python manage.py createsuperuser
```

7. **Сбор статических файлов**
```bash
python manage.py collectstatic --noinput
```

8. **Запуск сервера разработки**
```bash
python manage.py runserver
```

### Настройка Proxmox

1. Создайте API токен в Proxmox:
   - Datacenter → Permissions → API Tokens
   - Создайте токен для пользователя `root@pam`
   - Сохраните токен в `.env`

2. Создайте шаблоны VM для заданий:
   - Установите cloud-init на VM
   - Настройте qemu-guest-agent
   - Конвертируйте VM в шаблон

3. Настройте SSH-доступ от Django-сервера к Proxmox (для выполнения команд в VM):
```bash
ssh-keygen -t rsa
ssh-copy-id root@10.100.0.254
```

### Настройка OpenVPN

1. **Запуск OpenVPN в Docker**
```bash
docker run -v /var/www/hxctf/openvpn-data:/etc/openvpn \
  --name openvpn -d -p 1194:1194/udp \
  kylemanna/openvpn
```

2. **Инициализация PKI**
```bash
docker exec -it openvpn ovpn_genconfig -u udp://your-server-ip
docker exec -it openvpn ovpn_initpki
```

3. **Создание директории CCD**
```bash
mkdir -p /var/www/hxctf/openvpn-data/ccd
```

### Настройка Celery (опционально)

Для автоматической очистки просроченных VM:

1. **Запуск Redis**
```bash
sudo systemctl start redis
```

2. **Запуск Celery Worker**
```bash
celery -A hxctf worker -l info
```

3. **Запуск Celery Beat**
```bash
celery -A hxctf beat -l info
```

Или используйте management-команду:
```bash
python manage.py cleanup_expired_vms
```

## Использование

### Создание задания

1. Войдите в админ-панель: `/admin/`
2. Перейдите в раздел "Задания"
3. Нажмите "Добавить задание"
4. Заполните поля:
   - **Название**: краткое название задания
   - **Описание**: краткое описание (отображается в списке)
   - **README файл**: загрузите HTML или PDF с полным описанием
   - **Тип задания**: выберите `file` или `vm`
   - **Файл**: для файловых заданий — загрузите файл
   - **ID шаблона в Proxmox**: для VM-заданий — укажите ID шаблона
   - **Баллы**: количество баллов за задание

5. Создайте флаги для задания:
   - Для файловых заданий: укажите статичный флаг в поле `flag_value`
   - Для VM-заданий: укажите `file_path` (путь в VM, куда будет вставлен флаг)

### Работа с VM

**Как это работает:**

1. Участник нажимает "Запустить VM" на странице задания
2. Система:
   - Клонирует шаблон VM из Proxmox
   - Назначает уникальный IP из подсети пользователя (`10.100.X.101-250`)
   - Запускает VM
   - Ждёт готовности VM (проверка через qemu-guest-agent)
   - Генерирует уникальные флаги (формат: `flag{32-символа}`)
   - Вставляет флаги в указанные файлы через SSH
   - Сохраняет флаги в базе данных

3. VM работает 60 минут, затем автоматически удаляется

**Генерация VM ID:**
- Формат: `8 + UserID + 00 + TaskID`
- Пример: пользователь 7, задание 12 → VM ID = `8712`

### Управление регистрацией

В админ-панели → "Настройки регистрации":
- **Регистрация открыта**: включить/выключить регистрацию
- **Закроется в**: установить дату/время автоматического закрытия

### VPN для участников

1. Участник заходит на главную страницу
2. Нажимает "Скачать VPN конфиг"
3. Система:
   - Назначает уникальную подсеть (`10.100.X.0/24`)
   - Генерирует сертификат OpenVPN
   - Создаёт CCD-файл с маршрутом к подсети
   - Отдаёт `.ovpn` файл

4. Участник подключается через OpenVPN и получает доступ к своим VM

## API и интеграции

### Proxmox API

Класс `ProxmoxClient` (vms/proxmox_client.py) предоставляет методы:

- `clone_vm(template_id, new_vm_id)` — клонирование шаблона
- `set_ip(vm_id, ip_address)` — установка IP через cloud-init
- `start_vm(vm_id)` — запуск VM
- `stop_vm(vm_id)` — остановка VM
- `destroy_vm(vm_id)` — удаление VM
- `exec_command(vm_id, command)` — выполнение команды в VM через SSH

### Автоматизация

**Очистка просроченных VM:**

Вариант 1 — Celery (рекомендуется):
```python
# vms/tasks.py
@shared_task
def cleanup_expired_vms():
    # Автоматически запускается по расписанию
```

Вариант 2 — Cron:
```bash
*/5 * * * * cd /var/www/hxctf && python manage.py cleanup_expired_vms
```

## Безопасность

### Реализованные меры

1. **Изоляция пользователей**: каждый участник получает свою подсеть
2. **Уникальные флаги**: флаги генерируются индивидуально для каждого участника
3. **Таймауты VM**: автоматическое удаление через 60 минут
4. **Модерация**: регистрация требует одобрения администратором
5. **CSRF-защита**: включена в Django
6. **Сессии**: таймаут 30 минут

### Рекомендации

- Используйте HTTPS в продакшене
- Смените `SECRET_KEY` на случайный
- Настройте `ALLOWED_HOSTS` в settings.py
- Используйте PostgreSQL вместо SQLite
- Настройте firewall на Proxmox-сервере
- Регулярно обновляйте зависимости

## Мониторинг

### Админ-панель

Доступна по адресу `/admin/monitoring/`:
- Список всех запущенных VM
- Статус VM (running/stopped/destroyed)
- Время запуска и окончания
- IP-адреса

### Логи

Логи выполнения команд в Proxmox выводятся в консоль:
```
[Proxmox] → Клонируем шаблон 100 → VM 8712
[Proxmox] → Устанавливаем IP 10.100.67.101 для VM 8712
[VM] Ожидаем готовности VM 8712...
[VM] Флаг вставлен в /root/flag.txt для user123
```

## Troubleshooting

### VM не запускается

1. Проверьте доступность Proxmox API:
```bash
curl -k https://10.100.0.254:8006/api2/json/version
```

2. Проверьте SSH-доступ к Proxmox:
```bash
ssh root@10.100.0.254 "qm list"
```

3. Проверьте логи Django:
```bash
tail -f /var/log/django/error.log
```

### Флаги не вставляются в VM

1. Убедитесь, что в VM установлен `qemu-guest-agent`:
```bash
apt install qemu-guest-agent
systemctl enable qemu-guest-agent
```

2. Проверьте, что VM-шаблон имеет включённый guest agent в Proxmox

3. Увеличьте таймаут ожидания готовности VM в `vms/views.py` (строка 96)

### VPN не подключается

1. Проверьте статус OpenVPN-контейнера:
```bash
docker ps | grep openvpn
docker logs openvpn
```

2. Проверьте, что порт 1194/udp открыт:
```bash
sudo ufw allow 1194/udp
```

3. Проверьте CCD-файлы:
```bash
ls -la /var/www/hxctf/openvpn-data/ccd/
```

## Производительность

### Рекомендуемые характеристики сервера

**Для Django-приложения:**
- CPU: 2+ ядра
- RAM: 4+ GB
- Disk: 20+ GB SSD

**Для Proxmox:**
- CPU: 8+ ядер (зависит от количества одновременных VM)
- RAM: 32+ GB (2-4 GB на VM × количество участников)
- Disk: 500+ GB SSD

### Оптимизация

1. Используйте PostgreSQL с connection pooling
2. Настройте кэширование Django (Redis/Memcached)
3. Используйте CDN для статических файлов
4. Настройте Nginx как reverse proxy
5. Используйте Gunicorn/uWSGI вместо runserver

## Лицензия

Проект разработан для образовательных целей.

## Поддержка

При возникновении проблем проверьте:
1. Логи Django
2. Логи Proxmox (`/var/log/pve/`)
3. Логи OpenVPN (`docker logs openvpn`)
4. Статус Celery worker (если используется)

---

**Версия:** 1.0  
**Последнее обновление:** 2026-05-21
