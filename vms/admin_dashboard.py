from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.conf import settings
from proxmoxer import ProxmoxAPI
import psutil
from datetime import datetime
import json
from collections import deque

from django.contrib.sessions.models import Session
from django.utils import timezone

from vms.models import UserVMInstance
from tasks.models import Task
from django.contrib.auth import get_user_model

User = get_user_model()

# История для графиков
HISTORY_SIZE = 30
cpu_history = deque(maxlen=HISTORY_SIZE)
ram_history = deque(maxlen=HISTORY_SIZE)
timestamps = deque(maxlen=HISTORY_SIZE)
history_initialized = False


@staff_member_required
def proxmox_dashboard(request):
    global cpu_history, ram_history, timestamps, history_initialized

    now = datetime.now().strftime("%H:%M:%S")

    # ==================== Proxmox ====================
    try:
        proxmox = ProxmoxAPI(
            host=settings.PROXMOX_HOST,
            user="root@pam",
            token_name="ctf-platform",
            token_value=settings.PROXMOX_TOKEN_SECRET,
            verify_ssl=False,
            port=8006
        )
        node = settings.PROXMOX_NODE
        node_status = proxmox.nodes(node).status.get()

        cpu_proxmox = round(float(node_status.get('cpu', 0) or 0) * 100, 1)
        memory_info = node_status.get('memory', {})
        mem_used = float(memory_info.get('used', 0) or 0) / (1024**3)
        mem_total = float(memory_info.get('total', 0) or 0) / (1024**3)
        ram_proxmox = round((mem_used / mem_total * 100) if mem_total > 0 else 0, 1)
    except:
        cpu_proxmox = 0
        ram_proxmox = 0

    # ==================== Django ====================
    try:
        cpu_django = round(psutil.cpu_percent(interval=0.3), 1)
        mem = psutil.virtual_memory()
        ram_django = round(mem.percent, 1)
    except:
        cpu_django = 0
        ram_django = 0

    # ==================== История для графиков ====================
    if not history_initialized:
        for _ in range(HISTORY_SIZE):
            cpu_history.append([cpu_proxmox, cpu_django])
            ram_history.append([ram_proxmox, ram_django])
            timestamps.append(now)
        history_initialized = True
    else:
        cpu_history.append([cpu_proxmox, cpu_django])
        ram_history.append([ram_proxmox, ram_django])
        timestamps.append(now)

    # ==================== Статистика ====================
    try:
        stats = {
            'total_users': User.objects.count(),
            'approved_users': User.objects.filter(is_approved=True).count(),
            'active_vms': UserVMInstance.objects.filter(status='running').count(),
            'total_tasks': Task.objects.filter(is_active=True).count(),
        }
    except:
        stats = {'total_users': 0, 'approved_users': 0, 'active_vms': 0, 'total_tasks': 0}

    # ==================== Активные сессии (онлайн) ====================
    try:
        active_sessions = Session.objects.filter(expire_date__gt=timezone.now()).count()
    except:
        active_sessions = 0

    context = {
        'cpu_proxmox': cpu_proxmox,
        'cpu_django': cpu_django,
        'ram_proxmox': ram_proxmox,
        'ram_django': ram_django,
        'stats': stats,
        'active_sessions': active_sessions,
        'last_updated': now,
        'timestamps': json.dumps(list(timestamps)),
        'cpu_data': json.dumps(list(cpu_history)),
        'ram_data': json.dumps(list(ram_history)),
    }
    return render(request, 'admin/proxmox_dashboard.html', context)
