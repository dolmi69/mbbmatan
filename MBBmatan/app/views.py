from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.views import LoginView
from .forms import RegisterForm, LoginForm
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Note, ChatMessage, ChatRoom
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import FavoriteFormula
from django.http import JsonResponse
from .models import FormulaQuestion, TestAttempt
import random
from .models import UserProfile
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import FriendRequest


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


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'registration/login.html'


def profile(request):
    if request.user.is_authenticated:
        attempts = TestAttempt.objects.filter(user=request.user).order_by('-date')[:5] #отвечает за количество вопросов в тесте
        favorites = FavoriteFormula.objects.filter(user=request.user)

        context = {
            'user': request.user,
            'attempts': attempts,
            'total_attempts': attempts.count(),
            'total_correct': sum([a.correct_answers for a in attempts]),
            'favorites': favorites,
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
    if 'quiz_questions' not in request.session:
        all_questions = list(FormulaQuestion.objects.all())

        if len(all_questions) < 5:
            return render(request, 'error.html', {'message': 'Недостаточно вопросов для теста'})

        request.session['quiz_questions'] = [q.id for q in random.sample(all_questions, 5)]
        request.session['current_question'] = 0
        request.session['score'] = 0

    question_ids = request.session['quiz_questions']
    current_idx = request.session['current_question']

    if current_idx >= len(question_ids):
        return redirect('app:quiz_result')

    try:
        question = FormulaQuestion.objects.get(id=question_ids[current_idx])
    except FormulaQuestion.DoesNotExist:
        return redirect('app:quiz_result')

    if request.method == 'POST':
        user_answer = request.POST.get('answer')
        if user_answer == question.correct_answer:
            request.session['score'] += 1

        request.session['current_question'] += 1
        request.session.modified = True

        if request.session['current_question'] >= len(question_ids):
            return redirect('app:quiz_result')

        return redirect('app:formula_quiz')

    return render(request, 'formuls/quiz.html', {
        'question': question,
        'current_number': current_idx + 1,
        'total_questions': len(question_ids)
    })


def quiz_result(request):
    if 'quiz_questions' not in request.session:
        return redirect('app:formula_quiz')

    score = request.session.get('score', 0)
    total = len(request.session['quiz_questions'])

    if request.user.is_authenticated:
        TestAttempt.objects.create(
            user=request.user,
            correct_answers=score,
            total_questions=total
        )

    del request.session['quiz_questions']
    del request.session['current_question']
    del request.session['score']

    return render(request, 'formuls/quiz_result.html', {
        'score': score,
        'total': total,
        'progress': int((score / total) * 100) if total > 0 else 0
    })


'''
@login_required
def enhanced_profile(request):
    profile = request.user.profile
    active_quests = UserQuest.objects.filter(
        user=request.user,
        is_completed=False
    ).select_related('quest')

    exp_needed = profile.level * 100
    exp_progress = min((profile.experience / exp_needed) * 100, 100)

    context = {
        'profile': profile,
        'active_quests': active_quests,
        'exp_needed': exp_needed,
        'exp_progress': exp_progress,
        'success_rate': profile.success_rate(),
    }
    return render(request, 'profile_enhanced.html', context)'''


@login_required
def chat_home(request):
    rooms = ChatRoom.objects.filter(
        participants=request.user,
        is_active=True
    )
    general_rooms = ChatRoom.objects.filter(
        room_type__in=['general', 'physics', 'algebra', 'geometry'],
        is_active=True
    )

    return render(request, 'chat/home.html', {
        'user_rooms': rooms,
        'general_rooms': general_rooms,
    })


@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id, is_active=True)

    if room.room_type == 'private' and request.user not in room.participants.all():
        return redirect('app:chat_home')

    messages = ChatMessage.objects.filter(room=room)[:50]

    return render(request, 'chat/room.html', {
        'room': room,
        'messages': messages,
    })



def f_f(request):
    return render(request, 'formuls/f-f.html')

def t_f(request):
    return render(request, 'formuls/physics.html')

def t_a(request):
    return render(request, 'formuls/algebra.html')

def t_g(request):
    return render(request, 'formuls/geometry.html')


@login_required
def manage_friends(request):
    """Основная страница друзей (заявки и список)"""
    # Создаём профиль, если его нет
    if not hasattr(request.user, 'profile'):
        UserProfile.objects.create(user=request.user)

    # Получаем список друзей
    friends_profiles = request.user.profile.friends.all()
    friends = [profile.user for profile in friends_profiles]

    # Получаем заявки в друзья (входящие)
    received_requests = FriendRequest.objects.filter(
        to_user=request.user,
        status='pending'
    )

    # Получаем отправленные заявки (исходящие)
    sent_requests = FriendRequest.objects.filter(
        from_user=request.user,
        status='pending'
    )

    context = {
        'friends': friends,
        'received_requests': received_requests,
        'sent_requests': sent_requests,
    }
    return render(request, 'friends.html', context)


@login_required
def send_friend_request(request):
    """Отправка заявки в друзья"""
    if request.method == 'POST':
        username = request.POST.get('username')

        if username == request.user.username:
            messages.error(request, 'Нельзя отправить заявку самому себе')
            return redirect('app:manage_friends')

        try:
            target_user = User.objects.get(username=username)

            # Проверяем, уже ли друзья
            if hasattr(request.user, 'profile') and hasattr(target_user, 'profile'):
                if target_user.profile in request.user.profile.friends.all():
                    messages.info(request, f'Вы уже друзья с {username}')
                    return redirect('app:manage_friends')

            # Проверяем, не отправил ли уже заявку
            existing_request = FriendRequest.objects.filter(
                from_user=request.user,
                to_user=target_user,
                status='pending'
            ).exists()

            if existing_request:
                messages.info(request, f'Вы уже отправили заявку {username}')
                return redirect('app:manage_friends')

            # Проверяем, не отправил ли заявку целевой пользователь
            reverse_request = FriendRequest.objects.filter(
                from_user=target_user,
                to_user=request.user,
                status='pending'
            ).first()

            if reverse_request:
                # Если есть встречная заявка — сразу принимаем её
                reverse_request.accept()
                messages.success(request, f'Вы приняли заявку от {username} и стали друзьями!')
            else:
                # Создаём новую заявку
                FriendRequest.objects.create(
                    from_user=request.user,
                    to_user=target_user
                )
                messages.success(request, f'Заявка отправлена пользователю {username}')

        except User.DoesNotExist:
            messages.error(request, 'Пользователь не найден')

    return redirect('app:manage_friends')


@login_required
def handle_friend_request(request, request_id, action):
    """Обработка заявки в друзья (принять/отклонить)"""
    try:
        friend_request = FriendRequest.objects.get(
            id=request_id,
            to_user=request.user,
            status='pending'
        )

        if action == 'accept':
            if friend_request.accept():
                messages.success(request, f'Вы приняли заявку от {friend_request.from_user.username}')
            else:
                messages.error(request, 'Не удалось принять заявку')

        elif action == 'reject':
            if friend_request.reject():
                messages.info(request, f'Вы отклонили заявку от {friend_request.from_user.username}')
            else:
                messages.error(request, 'Не удалось отклонить заявку')

        elif action == 'cancel':
            # Отмена своей отправленной заявки
            if friend_request.from_user == request.user:
                friend_request.delete()
                messages.info(request, 'Заявка отменена')

    except FriendRequest.DoesNotExist:
        messages.error(request, 'Заявка не найдена')

    return redirect('app:manage_friends')


@login_required
def remove_friend(request):
    """Удаление из друзей"""
    if request.method == 'POST':
        username = request.POST.get('username')

        try:
            target_user = User.objects.get(username=username)

            if hasattr(request.user, 'profile') and hasattr(target_user, 'profile'):
                if target_user.profile in request.user.profile.friends.all():
                    request.user.profile.friends.remove(target_user.profile)
                    target_user.profile.friends.remove(request.user.profile)
                    messages.success(request, f'Вы удалили {username} из друзей')
                else:
                    messages.error(request, 'Этот пользователь не в вашем списке друзей')

        except User.DoesNotExist:
            messages.error(request, 'Пользователь не найден')

    return redirect('app:manage_friends')