from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

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


class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.message[:30]}..."



"""
class Quest(models.Model):
    QUEST_TYPES = [
        ('daily', 'Ежедневный'),
        ('weekly', 'Недельный'),
        ('seasonal', 'Сезонный'),
        ('achievement', 'Достижение'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    quest_type = models.CharField(max_length=20, choices=QUEST_TYPES, default='daily')
    reward_points = models.IntegerField(default=10)
    reward_experience = models.IntegerField(default=50)

    required_actions = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

class UserQuest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE)
    progress = models.JSONField(default=dict)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'quest']
"""



@receiver(post_migrate)
def create_initial_questions(sender, **kwargs):
    if hasattr(sender, 'name') and sender.name == 'app':
        try:
            from django.db import transaction

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
            ]

            if not FormulaQuestion.objects.exists():
                with transaction.atomic():
                    for q in initial_questions[:2]:  # Только 2 для начала
                        FormulaQuestion.objects.get_or_create(
                            formula=q['formula'],
                            defaults={
                                'correct_answer': q['correct_answer'],
                                'options': q['options']
                            }
                        )
        except Exception as e:
            pass



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