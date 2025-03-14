from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import RegisterForm, LoginForm
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Note
from django.contrib.auth.mixins import LoginRequiredMixin


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'registration/signup.html'
    success_url = '/accounts/login/'

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

def home(request):
    context = {
        'message': 'Добро пожаловать на главную страницу!',
    }
    return render(request, 'index.html', context)

def f_f(request):
    return render(request, 'formuls/f-f.html')

def t_a(request):
    return render(request, 'formuls/algebra.html')

def t_g(request):
    return render(request, 'formuls/geometry.html')

def t_f(request):
    return render(request, 'formuls/physics.html')


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'registration/login.html'


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'

class NoteListView(LoginRequiredMixin, ListView):
    model = Note
    template_name = "app/note_list.html"
    context_object_name = "notes"

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user)

class NoteCreateView(LoginRequiredMixin, CreateView):
    model = Note
    fields = ["title", "content"]
    template_name = "app/note_form.html"
    success_url = reverse_lazy("app:note_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class NoteUpdateView(LoginRequiredMixin, UpdateView):
    model = Note
    fields = ["title", "content"]
    template_name = "app/note_form.html"
    success_url = reverse_lazy("app:note_list")

class NoteDeleteView(LoginRequiredMixin, DeleteView):
    model = Note
    success_url = reverse_lazy("app:note_list")