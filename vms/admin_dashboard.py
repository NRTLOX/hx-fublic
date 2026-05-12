from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.conf import settings
from proxmoxer import ProxmoxAPI
import psutil
from datetime import datetime
import json

from vms.models import UserVMInstance
from tasks.models import Task
from django.contrib.auth import get_user_model

User = get_user_model()


@staff_member_required
def proxmox_dashboard(request):
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

        cpu_percent = round(float(node_status.get('cpu', 0) or 0) * 100, 1)
        cpu_free = round(100 - cpu_percent, 1)

        memory_info = node_status.get('memory', {})
        mem_used = round(float(memory_info.get('used', 0) or 0) / (1024**3), 1)
        mem_total = round(float(memory_info.get('total', 0) or 0) / (1024**3), 1)
        mem_percent = round((mem_used / mem_total * 100) if mem_total > 0 else 0, 1)
        mem_free = round(100 - mem_percent, 1)

        load_avg = node_status.get('loadavg', [0, 0, 0])
        load_1 = round(float(load_avg[0] or 0), 2)
        load_5 = round(float(load_avg[1] or 0), 2)
        load_15 = round(float(load_avg[2] or 0), 2)

        uptime_seconds = node_status.get('uptime', 0)
        uptime_days = uptime_seconds // 86400
        uptime_hours = (uptime_seconds % 86400) // 3600

        proxmox_data = {
            'cpu_percent': cpu_percent,
            'cpu_free': cpu_free,
            'mem_used': mem_used,
            'mem_total': mem_total,
            'mem_percent': mem_percent,
            'mem_free': mem_free,
            'load_1': load_1,
            'load_5': load_5,
            'load_15': load_15,
            'uptime_days': uptime_days,
            'uptime_hours': uptime_hours,
            'node_name': node,
            'status': 'online'
        }
    except Exception as e:
        proxmox_data = {'status': 'error', 'error_message': str(e)}

    # ==================== Django Server ====================
    try:
        cpu = round(psutil.cpu_percent(interval=0.5), 1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        django_data = {
            'cpu_percent': cpu,
            'mem_percent': round(mem.percent, 1),
            'disk_percent': round(disk.percent, 1),
        }
    except:
        django_data = {'cpu_percent': 0, 'mem_percent': 0, 'disk_percent': 0}

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

    context = {
        'proxmox': proxmox_data,
        'django': django_data,
        'stats': stats,
        'last_updated': datetime.now().strftime("%H:%M:%S"),
        'load_labels': json.dumps(['1 мин', '5 мин', '15 мин']),
        'load_values': json.dumps([proxmox_data.get('load_1', 0), 
                                   proxmox_data.get('load_5', 0), 
                                   proxmox_data.get('load_15', 0)]),
    }
    return render(request, 'admin/proxmox_dashboard.html', context)
