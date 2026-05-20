from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.db.models import Q
from django.contrib.auth import get_user_model
User = get_user_model()
import subprocess
from django.http import HttpResponse

def home(request):
    if request.user.is_authenticated:
        if not request.user.is_approved:
            return render(request, 'core/not_approved.html')
        
        # Проверяем, есть ли уже VPN конфиг у пользователя
        has_vpn = hasattr(request.user, 'vpn_client') and request.user.vpn_client.is_active
        
        return render(request, 'core/home.html', {'has_vpn': has_vpn})
    
    return render(request, 'core/landing.html')

def register_view(request):
    from .models import RegistrationSettings
    from django.utils import timezone

    # Проверяем настройки регистрации
    settings = RegistrationSettings.get_settings()

    # Если регистрация закрыта
    if not settings.is_open:
        messages.error(request, 'Регистрация временно закрыта.')
        return redirect('login')

    # Если регистрация открыта на время и время истекло
    if settings.closes_at and timezone.now() > settings.closes_at:
        settings.is_open = False
        settings.closes_at = None
        settings.save()
        messages.error(request, 'Регистрация закрыта.')
        return redirect('login')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_approved = False
            user.save()

            # Автоматически создаём запись о подсети (пока без конкретной подсети)
            # Подсеть будет назначена при первой генерации VPN конфига
            messages.success(request, 'Регистрация прошла успешно! Ожидайте одобрения администратора.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_approved:
                messages.error(request, 'Ваш аккаунт ещё не одобрен администратором.')
                return redirect('login')
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

from django.db.models import Sum, Count
from tasks.models import Submission, Task

@login_required
def profile(request):
    if not request.user.is_approved:
        return redirect('home')

    # Все успешно сданные флаги пользователя
    correct_submissions = Submission.objects.filter(
        user=request.user, 
        is_correct=True
    ).select_related('task', 'flag')

    # Общее количество баллов
    total_points = correct_submissions.aggregate(
        total=Sum('task__points')
    )['total'] or 0

    # Количество решённых заданий
    solved_tasks_count = correct_submissions.values('task').distinct().count()

    context = {
        'user': request.user,
        'total_points': total_points,
        'solved_tasks_count': solved_tasks_count,
        'submissions': correct_submissions.order_by('-submitted_at')[:20],  # последние 20
    }
    return render(request, 'core/profile.html', context)


@login_required
def leaderboard(request):
    if not request.user.is_approved:
        return redirect('home')

    # Топ пользователей по баллам
    leaderboard_data = User.objects.filter(
        is_approved=True
    ).annotate(
        points=Sum('submission__task__points', filter=Q(submission__is_correct=True)),
        solved=Count('submission', filter=Q(submission__is_correct=True), distinct=True)
    ).order_by('-points', '-solved')[:50]

    # Позиция текущего пользователя
    user_rank = None
    for idx, entry in enumerate(leaderboard_data):
        if entry.id == request.user.id:
            user_rank = idx + 1
            break

    context = {
        'leaderboard': leaderboard_data,
        'user_rank': user_rank,
    }
    return render(request, 'core/leaderboard.html', context)


import os
from django.http import HttpResponse
from django.contrib import messages
from .models import VPNClient
from .vpn_generator import VPNGenerator   # создадим этот файл ниже

@login_required
def download_vpn_config(request):
    if not request.user.is_approved:
        messages.error(request, "Ваш аккаунт ещё не одобрен.")
        return redirect('home')

    config = VPNGenerator.generate_ovpn_config(request.user)

    if not config:
        messages.error(request, "Не удалось сгенерировать VPN конфиг.")
        return redirect('home')

    filename = f"{request.user.username}_hxctf.ovpn"

    response = HttpResponse(config, content_type='application/x-openvpn-profile')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    messages.success(request, f"VPN конфиг для {request.user.username} скачивается...")
    return response
