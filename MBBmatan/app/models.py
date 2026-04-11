from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.db import transaction
from .encryption import encrypt_message, decrypt_message

User = get_user_model()


class Note(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or f"Заметка #{self.id}"


class FavoriteFormula(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    formula_text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'formula_text']


class FormulaQuestion(models.Model):
    formula = models.CharField("Вопрос", max_length=200)
    correct_answer = models.CharField("Правильный ответ", max_length=200)
    options = models.JSONField("Варианты ответов", default=list)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    def __str__(self):
        return self.formula[:50] + "..." if len(self.formula) > 50 else self.formula


class TestAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    correct_answers = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)

    def success_percent(self):
        return round((self.correct_answers / self.total_questions) * 100, 2) if self.total_questions > 0 else 0


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    level = models.IntegerField(default=1)
    experience = models.IntegerField(default=0)
    points = models.IntegerField(default=0)

    total_questions_answered = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    total_formulas_studied = models.IntegerField(default=0)
    tests_completed = models.IntegerField(default=0)

    friends = models.ManyToManyField('self', symmetrical=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)

    show_statistics = models.BooleanField(default=True)
    notifications_enabled = models.BooleanField(default=True)

    def add_experience(self, amount):
        self.experience += amount
        self.check_level_up()
        self.save()

    def check_level_up(self):
        exp_needed = self.level * 100
        while self.experience >= exp_needed:
            self.level += 1
            self.experience -= exp_needed
            self.points += 50
            exp_needed = self.level * 100

    def add_test_completed(self, correct_answers, total_questions):
        self.total_questions_answered += total_questions
        self.correct_answers += correct_answers
        self.tests_completed += 1

        experience_gained = correct_answers * 10
        if correct_answers == total_questions:
            experience_gained += 50

        self.add_experience(experience_gained)
        self.save()

    def success_rate(self):
        if self.total_questions_answered > 0:
            return (self.correct_answers / self.total_questions_answered) * 100
        return 0

    def __str__(self):
        return f"{self.user.username} (Уровень {self.level})"


@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.profile.save()


class ChatRoom(models.Model):
    ROOM_TYPES = [
        ('general', 'Общий чат'),
        ('physics', 'Физика'),
        ('algebra', 'Алгебра'),
        ('geometry', 'Геометрия'),
        ('private', 'Приватный'),
        ('group', 'Групповой'),
    ]

    name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='general')
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    participants = models.ManyToManyField(User, related_name='chat_rooms', blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()})"

    def get_last_message(self):
        return self.messages.order_by('-timestamp').first()

    def get_unread_count(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()

    @classmethod
    def get_or_create_general_chats(cls):
        general_chats = [
            {
                'name': 'Общий чат по физике',
                'room_type': 'physics',
                'description': 'Обсуждение формул и законов физики'
            },
            {
                'name': 'Общий чат по алгебре',
                'room_type': 'algebra',
                'description': 'Обсуждение алгебраических выражений и уравнений'
            },
            {
                'name': 'Общий чат по геометрии',
                'room_type': 'geometry',
                'description': 'Обсуждение геометрических фигур и теорем'
            },
        ]

        for chat_data in general_chats:
            cls.objects.get_or_create(
                name=chat_data['name'],
                room_type=chat_data['room_type'],
                defaults={
                    'description': chat_data['description'],
                    'is_active': True
                }
            )

class ChatMessage(models.Model):
    room = models.ForeignKey('ChatRoom', on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    _message = models.TextField(db_column='message')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies'
    )

    @property
    def message(self):
        return decrypt_message(self._message)

    @message.setter
    def message(self, value):
        self._message = encrypt_message(value)

    def __str__(self):
        try:
            preview = self.message[:30] + '...' if len(self.message) > 30 else self.message
        except:
            preview = '***'
        return f"{self.sender.username}: {preview}"

    class Meta:
        ordering = ['timestamp']

@receiver(post_migrate)
def create_initial_data(sender, **kwargs):
    if hasattr(sender, 'name') and sender.name == 'app':
        try:
            initial_questions = [
                {
                    "formula": "Какая формула выражает закон Архимеда?",
                    "correct_answer": "F = ρ·g·V",
                    "options": ["F = m·a", "F = ρ·g·V", "P = F/S", "v = s/t"]
                },
                {
                    "formula": "Как называется единица измерения силы?",
                    "correct_answer": "Ньютон",
                    "options": ["Паскаль", "Джоуль", "Ньютон", "Ватт"]
                },
                {
                    "formula": "Формула для вычисления площади круга?",
                    "correct_answer": "S = π·r²",
                    "options": ["S = a·b", "S = π·r²", "S = ½·a·h", "S = a²"]
                },
                {
                    "formula": "Формула теоремы Пифагора?",
                    "correct_answer": "a² + b² = c²",
                    "options": ["E = mc²", "a² + b² = c²", "V = S·h", "F = G·(m₁·m₂)/r²"]
                },
                {
                    "formula": "Формула для вычисления скорости?",
                    "correct_answer": "v = s/t",
                    "options": ["v = s·t", "v = s/t", "v = a·t", "v = √(2gh)"]
                },
                {
                    "formula": "Формула для вычисления работы?",
                    "correct_answer": "A = F·s",
                    "options": ["A = F·s", "A = m·g·h", "A = P·t", "A = ½·m·v²"]
                },
                {
                    "formula": "Формула для вычисления мощности?",
                    "correct_answer": "P = A/t",
                    "options": ["P = F·v", "P = A/t", "P = U·I", "P = m·g"]
                },
            ]

            with transaction.atomic():
                for q in initial_questions:
                    FormulaQuestion.objects.get_or_create(
                        formula=q['formula'],
                        defaults={
                            'correct_answer': q['correct_answer'],
                            'options': q['options']
                        }
                    )

            ChatRoom.get_or_create_general_chats()

        except Exception as e:
            print(f"Error creating initial data: {e}")


class FriendRequest(models.Model):
    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_requests'
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_requests'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Ожидание'),
            ('accepted', 'Принята'),
            ('rejected', 'Отклонена'),
        ],
        default='pending'
    )

    class Meta:
        unique_together = ['from_user', 'to_user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.status})"

    def accept(self):
        if self.status == 'pending':
            if not hasattr(self.from_user, 'profile'):
                UserProfile.objects.create(user=self.from_user)
            if not hasattr(self.to_user, 'profile'):
                UserProfile.objects.create(user=self.to_user)

            self.from_user.profile.friends.add(self.to_user.profile)
            self.to_user.profile.friends.add(self.from_user.profile)
            self.status = 'accepted'
            self.save()
            return True
        return False

    def reject(self):
        if self.status == 'pending':
            self.status = 'rejected'
            self.save()
            return True
        return False



class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('friend_request', 'Заявка в друзья'),
        ('friend_accepted', 'Заявка принята'),
        ('chat_message', 'Новое сообщение'),
        ('test_completed', 'Тест пройден'),
        ('achievement', 'Достижение'),
        ('system', 'Системное'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    text = models.CharField(max_length=255)
    link = models.CharField(max_length=200, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.text[:50]}"