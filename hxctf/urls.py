from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve as serve_media
from vms.admin_dashboard import proxmox_dashboard, admin_stop_vm

urlpatterns = [
    path('admin/monitoring/', proxmox_dashboard, name='admin_monitoring'),
    path('admin/monitoring/stop/<int:instance_id>/', admin_stop_vm, name='admin_stop_vm'),

    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('tasks/', include('tasks.urls')),
    path('vms/', include('vms.urls')),
]

# Раздаём media (README, файлы заданий и т.д.) всегда, а не только при DEBUG.
# django.conf.urls.static.static() сама молча ничего не добавляет при DEBUG=False,
# поэтому подключаем django.views.static.serve напрямую, в обход этой проверки.
# Нет отдельного nginx перед media — раздачу берёт на себя сам Django.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve_media, {'document_root': settings.MEDIA_ROOT}),
]
