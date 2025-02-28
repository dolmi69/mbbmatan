from django.shortcuts import redirect
from django.views.generic import CreateView, TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import RegisterForm, LoginForm

class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'registration/signup.html'
    success_url = '/login/'

class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'registration/login.html'

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'