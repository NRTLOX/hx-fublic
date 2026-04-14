from django.urls import path
from . import views as task_views

urlpatterns = [
    path('', task_views.task_list, name='task_list'),
    path('<int:task_id>/', task_views.task_detail, name='task_detail'),
    path('<int:task_id>/submit/', task_views.submit_flag, name='submit_flag'),
]
