from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Task, Submission
from vms.models import UserVMInstance
from tasks.models import Task, Flag

    
@login_required
def task_list(request):
    if not request.user.is_approved:
        return redirect('home')
    
    tasks = Task.objects.filter(is_active=True).prefetch_related('flags')

    # Получаем список ID заданий, которые пользователь уже решил (хотя бы один правильный флаг)
    solved_task_ids = Submission.objects.filter(
        user=request.user,
        is_correct=True
    ).values_list('task_id', flat=True).distinct()

    context = {
        'tasks': tasks,
        'solved_task_ids': list(solved_task_ids),
    }
    return render(request, 'tasks/task_list.html', context)

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
    task = get_object_or_404(Task, id=task_id)
    vm_instance = UserVMInstance.objects.filter(
        user=request.user, 
        task=task, 
        status='running'
    ).first()

    if request.method == 'POST':
        submitted_text = request.POST.get('flag', '').strip()
        flag_id = request.POST.get('flag_id')

        if not submitted_text:
            messages.error(request, "Флаг не может быть пустым.")
            return redirect('task_detail', task_id=task.id)

        if not vm_instance:
            messages.error(request, "Виртуальная машина не запущена.")
            return redirect('task_detail', task_id=task.id)

        try:
            flag_obj = Flag.objects.get(id=flag_id, task=task)
            
            # Получаем сгенерированный флаг для этой VM
            saved_flag = vm_instance.generated_flags.get(str(flag_obj.id))

            # Проверяем, сдавал ли уже этот флаг пользователь
            existing_submission = Submission.objects.filter(
                user=request.user, 
                flag=flag_obj
            ).first()

            if saved_flag and saved_flag.strip() == submitted_text:
                # Правильный флаг
                if existing_submission and existing_submission.is_correct:
                    messages.warning(request, "Этот флаг уже был успешно сдан ранее.")
                else:
                    # Создаём или обновляем запись
                    if existing_submission:
                        existing_submission.is_correct = True
                        existing_submission.submitted_flag = submitted_text
                        existing_submission.save()
                    else:
                        Submission.objects.create(
                            user=request.user,
                            task=task,
                            flag=flag_obj,
                            submitted_flag=submitted_text,
                            is_correct=True
                        )
                    messages.success(request, f"✅ Флаг принят! +{task.points} баллов")
            else:
                # Неправильный флаг
                if not existing_submission:
                    Submission.objects.create(
                        user=request.user,
                        task=task,
                        flag=flag_obj,
                        submitted_flag=submitted_text,
                        is_correct=False
                    )
                messages.error(request, "❌ Неверный флаг.")
                
        except Flag.DoesNotExist:
            messages.error(request, "Флаг не найден.")
        except Exception as e:
            print(f"[Submit Flag Error] {e}")
            messages.error(request, "Произошла ошибка при проверке флага.")

    return redirect('task_detail', task_id=task.id)
