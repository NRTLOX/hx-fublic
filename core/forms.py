from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import Group
from .models import User


class CustomUserCreationForm(UserCreationForm):
    # Дропдаун вместо текстового поля. Список групп фильтруется в __init__,
    # чтобы учесть группы, закрытые для регистрации в их настройках.
    group = forms.ModelChoiceField(
        queryset=Group.objects.none(),
        required=False,
        label="Группа",
        empty_label="Без группы"
    )

    class Meta:
        model = User
        fields = ['username', 'full_name', 'group', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Группа доступна при регистрации, если для неё явно не выключили это в настройках
        self.fields['group'].queryset = Group.objects.exclude(
            registration_settings__is_open_for_registration=False
        )
        # Делаем поля красивее
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Имя пользователя'})
        self.fields['full_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'ФИО'})
        self.fields['group'].widget.attrs.update({'class': 'form-select'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Пароль'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Повторите пароль'})

    def save(self, commit=True):
        user = super().save(commit=False)
        selected_group = self.cleaned_data.get('group')
        # Старое текстовое поле оставляем в синхроне для админки/поиска
        user.group = selected_group.name if selected_group else ''
        if commit:
            user.save()
            if selected_group:
                user.groups.add(selected_group)
        return user


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Имя пользователя'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Пароль'
        })
