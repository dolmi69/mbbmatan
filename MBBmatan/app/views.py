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
from .models import FavoriteFormula
from django.http import JsonResponse
from django.utils import timezone
from .models import FormulaQuestion, TestAttempt


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('app:login')

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

def da(request):
    return render(request, 'da.html')

def t_f(request):
    return render(request, 'formuls/physics.html')


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'registration/login.html'


def profile(request):
    if request.user.is_authenticated:
        attempts = TestAttempt.objects.filter(user=request.user).order_by('-date')[:5]
        favorites = FavoriteFormula.objects.filter(user=request.user)  # Новая строка

        context = {
            'user': request.user,
            'attempts': attempts,
            'total_attempts': attempts.count(),
            'total_correct': sum([a.correct_answers for a in attempts]),
            'favorites': favorites,  # Добавляем в контекст
        }
        return render(request, 'profile.html', context)
    return redirect('login')

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




def toggle_favorite(request):
    if request.method == 'POST' and request.user.is_authenticated:
        formula_text = request.POST.get('formula_text')
        favorite, created = FavoriteFormula.objects.get_or_create(
            user=request.user,
            formula_text=formula_text
        )
        if not created:
            favorite.delete()
            return JsonResponse({'status': 'removed'})
        return JsonResponse({'status': 'added'})
    return JsonResponse({'status': 'error'}, status=400)


def profile(request):
    if request.user.is_authenticated:
        attempts = TestAttempt.objects.filter(user=request.user).order_by('-date')[:5] #отображаем последнии 5 попыток можем менять как хотим
        total_attempts = attempts.count()
        total_correct = sum([a.correct_answers for a in attempts])

        context = {
            'user': request.user,
            'attempts': attempts,
            'total_attempts': total_attempts,
            'total_correct': total_correct,
        }
        return render(request, 'profile.html', context)
    return redirect('/accounts/login/')

def physics_formulas(request):
    formulas = [
        {'text': 'E = mc<sup>2</sup>'},
        {'text': 'F = ma'},
        {'text': 'V = IR'}
    ]

    if request.user.is_authenticated:
        user_favorites = FavoriteFormula.objects.filter(
            user=request.user
        ).values_list('formula_text', flat=True)

        for formula in formulas:
            formula['is_favorite'] = formula['text'] in user_favorites

    return render(request, 'f-f.html', {'formulas': formulas})


def formula_quiz(request):
    all_questions = FormulaQuestion.objects.all()
    if all_questions.count() < 5:
        return render(request, 'error.html', {
            'message': 'Для проведения теста требуется минимум 5 вопросов в базе'
        })
    if request.method == 'GET':
        random_questions = list(all_questions.order_by('?')[:5])
        request.session['quiz_questions'] = [q.id for q in random_questions]
        return render(request, 'formuls/quiz.html', {'questions': random_questions})

    elif request.method == 'POST':
        question_ids = request.session.get('quiz_questions', [])
        questions = FormulaQuestion.objects.filter(id__in=question_ids)

        score = 0
        total = len(questions)

        for question in questions:
            user_answer = request.POST.get(f'question_{question.id}')
            if user_answer == question.correct_answer:
                score += 1

        if request.user.is_authenticated:
            TestAttempt.objects.create(
                user=request.user,
                correct_answers=score,
                total_questions=total
            )

        progress = int((score / total) * 100) if total > 0 else 0

        if 'quiz_questions' in request.session:
            del request.session['quiz_questions']

        return render(request, 'formuls/quiz_result.html', {
            'score': score,
            'total': total,
            'progress': progress
        })