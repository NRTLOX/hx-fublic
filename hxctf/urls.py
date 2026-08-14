from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from vms.admin_dashboard import proxmox_dashboard, admin_stop_vm

urlpatterns = [
    path('admin/monitoring/', proxmox_dashboard, name='admin_monitoring'),
    path('admin/monitoring/stop/<int:instance_id>/', admin_stop_vm, name='admin_stop_vm'),

    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('tasks/', include('tasks.urls')),
    path('vms/', include('vms.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
