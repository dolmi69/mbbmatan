from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')

class LoginForm(AuthenticationForm):
    pass


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label="Имя пользователя",
        max_length=150,
        help_text="Обязательно. Не более 150 символов. Только буквы, цифры и @/./+/-/_."
    )

    password1 = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput,
        help_text="Пароль должен содержать минимум 8 символов."
    )

    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput,
        strip=False,
        help_text="Повторите пароль для проверки."
    )

    email = forms.EmailField(
        label="Электронная почта",
        required=True
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")