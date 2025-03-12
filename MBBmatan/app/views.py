from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import RegisterForm, LoginForm
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm

class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'registration/signup.html'
    success_url = '/accounts/login/'

class SignUpView(CreateView):
    form_class = CustomUserCreationForm  # Используем нашу кастомную форму
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

def home(request):
    context = {
        'message': 'Добро пожаловать на главную страницу!',
    }
    return render(request, 'index.html', context)

class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'registration/login.html'


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'