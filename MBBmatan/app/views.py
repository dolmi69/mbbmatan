from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.views import LoginView
from django.views.decorators.http import require_POST
from .forms import RegisterForm, LoginForm, CustomUserCreationForm, GroupChatForm
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .models import (
    Note, ChatMessage, ChatRoom, FavoriteFormula, FormulaQuestion,
    TestAttempt, UserProfile, FriendRequest, User, Notification
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
import random
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('app:login')


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')


def home(request):
    return render(request, 'index.html')


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'registration/login.html'


@login_required
def profile(request):
    attempts = TestAttempt.objects.filter(user=request.user).order_by('-date')[:5]
    favorites = FavoriteFormula.objects.filter(user=request.user)
    context = {
        'attempts': attempts,
        'favorites': favorites,
    }
    return render(request, 'profile.html', context)


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


@login_required
@require_POST
def toggle_favorite(request):
    formula_text = request.POST.get('formula_text')
    favorite, created = FavoriteFormula.objects.get_or_create(
        user=request.user,
        formula_text=formula_text
    )
    if not created:
        favorite.delete()
        return JsonResponse({'status': 'removed'})
    return JsonResponse({'status': 'added'})


def formula_quiz(request):
    if 'quiz_questions' not in request.session:
        all_questions = list(FormulaQuestion.objects.all())
        if not all_questions:
            messages.error(request, 'Нет доступных вопросов.')
            return redirect('app:home')
        num_questions = min(len(all_questions), 7)
        selected_questions = random.sample(all_questions, num_questions)
        request.session['quiz_questions'] = [q.id for q in selected_questions]
        request.session['current_question'] = 0
        request.session['score'] = 0
        request.session['last_answer_correct'] = None

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
        is_correct = user_answer == question.correct_answer
        request.session['last_answer_correct'] = is_correct
        if is_correct:
            request.session['score'] += 1
        request.session['current_question'] += 1
        request.session.modified = True
        if request.session['current_question'] >= len(question_ids):
            return redirect('app:quiz_result')
        return redirect('app:formula_quiz')

    mascot_state = 'neutral'
    mascot_message = "Выберите правильный ответ!"
    if 'last_answer_correct' in request.session:
        if request.session['last_answer_correct'] is True:
            mascot_state = 'thumbs_up'
            mascot_message = "Правильно! Отличная работа!"
        elif request.session['last_answer_correct'] is False:
            mascot_state = 'wrong'
            mascot_message = "Неверно. Попробуйте еще раз!"

    return render(request, 'formuls/quiz.html', {
        'question': question,
        'current_number': current_idx + 1,
        'total_questions': len(question_ids),
        'mascot_state': mascot_state,
        'mascot_message': mascot_message,
    })


def quiz_result(request):
    if 'quiz_questions' not in request.session:
        return redirect('app:formula_quiz')
    score = request.session.get('score', 0)
    total = len(request.session['quiz_questions'])
    percentage = (score / total * 100) if total > 0 else 0

    if request.user.is_authenticated:
        TestAttempt.objects.create(
            user=request.user,
            correct_answers=score,
            total_questions=total
        )
        profile = request.user.profile
        profile.add_test_completed(score, total)

    if percentage >= 80:
        mascot_state = 'thumbs_up'
        result_message = 'Отличный результат! 🎉'
    elif percentage >= 60:
        mascot_state = 'neutral'
        result_message = 'Хорошая работа! 👍'
    else:
        mascot_state = 'wrong'
        result_message = 'Попробуйте еще раз! 💪'

    keys_to_delete = ['quiz_questions', 'current_question', 'score', 'last_answer_correct']
    for key in keys_to_delete:
        if key in request.session:
            del request.session[key]

    return render(request, 'formuls/quiz_result.html', {
        'score': score,
        'total': total,
        'progress': int(percentage),
        'mascot_state': mascot_state,
        'result_message': result_message,
    })


@login_required
def chat_home(request):
    general_chats = ChatRoom.objects.filter(
        room_type__in=['physics', 'algebra', 'geometry'],
        is_active=True
    )
    private_rooms = ChatRoom.objects.filter(
        room_type__in=['private', 'group'],
        participants=request.user,
        is_active=True
    )
    return render(request, 'chat/home.html', {
        'general_chats': general_chats,
        'private_rooms': private_rooms,
    })


@login_required
def subject_chat(request, subject):
    subject_map = {'physics': 'Физика', 'algebra': 'Алгебра', 'geometry': 'Геометрия'}
    if subject not in subject_map:
        return redirect('app:chat_home')
    room_name = f"Чат по {subject_map[subject].lower()}"
    room, created = ChatRoom.objects.get_or_create(
        name=room_name,
        room_type=subject,
        defaults={'description': f'Обсуждение {subject_map[subject].lower()}', 'is_active': True}
    )
    if request.user not in room.participants.all():
        room.participants.add(request.user)
    return redirect('app:chat_room', room_id=room.id)


@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
    if room.room_type == 'private' and request.user not in room.participants.all():
        messages.error(request, 'Нет доступа')
        return redirect('app:chat_home')
    if room.room_type in ['physics', 'algebra', 'geometry', 'group']:
        if request.user not in room.participants.all():
            room.participants.add(request.user)

    ChatMessage.objects.filter(room=room, is_read=False).exclude(sender=request.user).update(is_read=True)
    Notification.objects.filter(user=request.user, link=f'/chat/{room.id}/', is_read=False).update(is_read=True)

    messages_list = ChatMessage.objects.filter(room=room).select_related('sender', 'reply_to', 'reply_to__sender').order_by('timestamp')[:100]
    return render(request, 'chat/room.html', {
        'room': room,
        'messages': messages_list,
    })

@login_required
@require_POST
def send_message(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
    if request.user not in room.participants.all():
        return JsonResponse({'error': 'Нет доступа'}, status=403)

    message_text = request.POST.get('message', '').strip()
    if not message_text:
        return JsonResponse({'error': 'Пустое сообщение'}, status=400)

    reply_to_id = request.POST.get('reply_to')
    reply_to = None
    if reply_to_id:
        try:
            reply_to = ChatMessage.objects.get(id=reply_to_id, room=room)
        except ChatMessage.DoesNotExist:
            pass

    message = ChatMessage.objects.create(
        room=room,
        sender=request.user,
        message=message_text,
        reply_to=reply_to
    )

    if room.room_type in ['private', 'group']:
        for participant in room.participants.exclude(id=request.user.id):
            Notification.objects.create(
                user=participant,
                text=f'Новое сообщение от {request.user.username} в чате "{room.name}"',
                link=f'/chat/{room.id}/',
                notification_type='chat_message'
            )

    return JsonResponse({
        'success': True,
        'message_id': message.id,
        'sender': message.sender.username,
        'message': message.message,
        'timestamp': message.timestamp.strftime('%H:%M'),
        'reply_to': {
            'id': reply_to.id,
            'sender': reply_to.sender.username,
            'message': reply_to.message
        } if reply_to else None
    })

@login_required
def manage_friends(request):
    Notification.objects.filter(
        user=request.user,
        notification_type='friend_accepted',
        is_read=False
    ).update(is_read=True)
    if not hasattr(request.user, 'profile'):
        UserProfile.objects.create(user=request.user)
    friends_profiles = request.user.profile.friends.all()
    friends = [p.user for p in friends_profiles]
    received_requests = FriendRequest.objects.filter(to_user=request.user, status='pending')
    sent_requests = FriendRequest.objects.filter(from_user=request.user, status='pending')
    return render(request, 'friends.html', {
        'friends': friends,
        'received_requests': received_requests,
        'sent_requests': sent_requests,
    })


@login_required
@require_POST
def send_friend_request(request):
    username = request.POST.get('username')
    if username == request.user.username:
        messages.error(request, 'Нельзя отправить заявку самому себе')
        return redirect('app:manage_friends')
    try:
        target_user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, 'Пользователь не найден')
        return redirect('app:manage_friends')

    # Проверка, не друзья ли уже
    if hasattr(request.user, 'profile') and hasattr(target_user, 'profile'):
        if target_user.profile in request.user.profile.friends.all():
            messages.info(request, f'Вы уже друзья с {username}')
            return redirect('app:manage_friends')

    existing_request = FriendRequest.objects.filter(
        from_user=request.user, to_user=target_user, status='pending'
    ).exists()
    if existing_request:
        messages.info(request, f'Вы уже отправили заявку {username}')
        return redirect('app:manage_friends')

    reverse_request = FriendRequest.objects.filter(
        from_user=target_user, to_user=request.user, status='pending'
    ).first()
    if reverse_request:
        reverse_request.accept()
        messages.success(request, f'Вы приняли заявку от {username} и стали друзьями!')
    else:
        FriendRequest.objects.create(from_user=request.user, to_user=target_user)
        Notification.objects.create(
            user=target_user,
            text=f'Пользователь {request.user.username} хочет добавить вас в друзья',
            link='/friends/',
            notification_type='friend_request'
        )
        messages.success(request, f'Заявка отправлена {username}')
    return redirect('app:manage_friends')


@login_required
def handle_friend_request(request, request_id, action):
    try:
        friend_request = FriendRequest.objects.get(id=request_id, to_user=request.user, status='pending')
    except FriendRequest.DoesNotExist:
        messages.error(request, 'Заявка не найдена')
        return redirect('app:manage_friends')
    if action == 'accept':
        if friend_request.accept():
            Notification.objects.create(
                user=friend_request.from_user,
                text=f'{request.user.username} принял(а) вашу заявку в друзья',
                link='/friends/',
                notification_type='friend_accepted'
            )
            messages.success(request, f'Вы приняли заявку от {friend_request.from_user.username}')
        else:
            messages.error(request, 'Не удалось принять заявку')
    elif action == 'reject':
        if friend_request.reject():
            messages.info(request, f'Вы отклонили заявку от {friend_request.from_user.username}')
        else:
            messages.error(request, 'Не удалось отклонить заявку')
    elif action == 'cancel':
        if friend_request.from_user == request.user:
            friend_request.delete()
            messages.info(request, 'Заявка отменена')
    return redirect('app:manage_friends')


@login_required
@require_POST
def remove_friend(request):
    username = request.POST.get('username')
    try:
        target_user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, 'Пользователь не найден')
        return redirect('app:manage_friends')
    if hasattr(request.user, 'profile') and hasattr(target_user, 'profile'):
        if target_user.profile in request.user.profile.friends.all():
            request.user.profile.friends.remove(target_user.profile)
            target_user.profile.friends.remove(request.user.profile)
            messages.success(request, f'Вы удалили {username} из друзей')
        else:
            messages.error(request, 'Этот пользователь не в вашем списке друзей')
    return redirect('app:manage_friends')


@login_required
def start_private_chat(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    if other_user == request.user:
        return redirect('app:manage_friends')
    users = sorted([request.user, other_user], key=lambda u: u.id)
    room = ChatRoom.objects.filter(
        room_type='private',
        participants=users[0]
    ).filter(participants=users[1]).first()
    if not room:
        room = ChatRoom.objects.create(
            name=f"Чат: {users[0].username} и {users[1].username}",
            room_type='private',
            created_by=request.user
        )
        room.participants.add(users[0], users[1])
    return redirect('app:chat_room', room_id=room.id)


# Новые функции
def user_profile_view(request, user_id):
    profile_user = get_object_or_404(User, id=user_id)
    show_stats = profile_user.profile.show_statistics if hasattr(profile_user, 'profile') else True
    return render(request, 'user_profile.html', {'profile_user': profile_user, 'show_stats': show_stats})


@login_required
def create_group_chat(request):
    friends_profiles = request.user.profile.friends.all()
    friends = User.objects.filter(profile__in=friends_profiles)
    if request.method == 'POST':
        form = GroupChatForm(request.POST, friends=friends)
        if form.is_valid():
            room = ChatRoom.objects.create(
                name=form.cleaned_data['name'],
                description=form.cleaned_data.get('description', ''),
                room_type='group',
                created_by=request.user
            )
            room.participants.add(request.user)
            for friend in form.cleaned_data['friends']:
                room.participants.add(friend)
                Notification.objects.create(
                    user=friend,
                    text=f'Вас добавили в группу "{room.name}"',
                    link=f'/chat/{room.id}/',
                    notification_type='chat_message'
                )
            messages.success(request, f'Группа "{room.name}" создана!')
            return redirect('app:chat_room', room_id=room.id)
    else:
        form = GroupChatForm(friends=friends)
    return render(request, 'chat/create_group.html', {'form': form})


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user)
    return render(request, 'notifications.html', {'notifications': notifications})


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('app:notifications')


@login_required
def get_hint(request):
    question_ids = request.session.get('quiz_questions', [])
    current_idx = request.session.get('current_question', 0)
    if current_idx < len(question_ids):
        question = FormulaQuestion.objects.get(id=question_ids[current_idx])
        hint = f"Подсказка: правильный ответ начинается с буквы '{question.correct_answer[0]}' и содержит {len(question.correct_answer)} символов."
        return JsonResponse({'hint': hint})
    return JsonResponse({'hint': 'Нет активного вопроса'})


def f_f(request):
    favorites = []
    if request.user.is_authenticated:
        favorites = list(FavoriteFormula.objects.filter(user=request.user).values_list('formula_text', flat=True))
    import json
    return render(request, 'formuls/f-f.html', {'favorites_json': json.dumps(favorites)})

def t_f(request):
    return render(request, 'formuls/physics.html')


def t_a(request):
    return render(request, 'formuls/algebra.html')


def t_g(request):
    return render(request, 'formuls/geometry.html')

class NoteDetailView(LoginRequiredMixin, DetailView):
    model = Note
    template_name = 'app/note_detail.html'
    context_object_name = 'note'

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user)