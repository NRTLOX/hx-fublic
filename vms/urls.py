from django.urls import path
from . import views as vm_views

urlpatterns = [
    path('<int:task_id>/start/', vm_views.start_vm, name='vm_start'),
    path('<int:task_id>/stop/', vm_views.stop_vm, name='vm_stop'),
    path('<int:task_id>/reset-timer/', vm_views.reset_timer, name='vm_reset_timer'),
]
