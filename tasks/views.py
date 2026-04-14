from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Task, Submission
from vms.models import UserVMInstance


@login_required
def task_list(request):
    if not request.user.is_approved:
        return redirect('home')
    
    tasks = Task.objects.filter(is_active=True)
    return render(request, 'tasks/task_list.html', {'tasks': tasks})


@login_required
def task_detail(request, task_id):
    if not request.user.is_approved:
        return redirect('home')
    
    task = get_object_or_404(Task, id=task_id)

    # Если это VM-задание — передаём информацию о машине пользователя
    vm_instance = None
    if task.task_type == 'vm':
        vm_instance = UserVMInstance.objects.filter(
            user=request.user, 
            task=task
        ).first()

    return render(request, 'tasks/task_detail.html', {
        'task': task,
        'vm_instance': vm_instance
    })


    
@login_required
def submit_flag(request, task_id):
    if not request.user.is_approved:
        return redirect('home')
    
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == 'POST':
        submitted_text = request.POST.get('flag', '').strip()
        flag_id = request.POST.get('flag_id')

        flag_obj = None
        is_correct = False

        if flag_id:
            flag_obj = task.flags.filter(id=flag_id).first()

        if flag_obj:
            # Проверяем, сдавал ли уже этот флаг пользователь успешно
            already_solved = Submission.objects.filter(
                user=request.user,
                flag=flag_obj,
                is_correct=True
            ).exists()

            if already_solved:
                messages.info(request, '✅ Этот флаг уже принят ранее.')
                return redirect('task_detail', task_id=task.id)

            # Проверяем правильность
            if flag_obj.flag_value.strip() == submitted_text:
                is_correct = True

        else:
            # Если flag_id не передан — проверяем все флаги задания
            for f in task.flags.all():
                if f.flag_value.strip() == submitted_text:
                    flag_obj = f
                    # Проверяем, не сдан ли уже этот флаг
                    if Submission.objects.filter(user=request.user, flag=f, is_correct=True).exists():
                        messages.info(request, '✅ Этот флаг уже принят ранее.')
                        return redirect('task_detail', task_id=task.id)
                    is_correct = True
                    break

        # Создаём запись о попытке
        Submission.objects.create(
            user=request.user,
            task=task,
            flag=flag_obj,
            submitted_flag=submitted_text,
            is_correct=is_correct
        )

        if is_correct:
            messages.success(request, '✅ Флаг принят! Отлично!')
        else:
            messages.error(request, '❌ Неверный флаг.')

    return redirect('task_detail', task_id=task.id)
