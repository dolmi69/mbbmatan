from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.db import transaction
import markdown
from .encryption import encrypt_message, decrypt_message

User = get_user_model()


class Note(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField(blank=True)
    canvas_data = models.TextField(blank=True)
    content_html = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.content:
            self.content_html = markdown.markdown(
                self.content,
                extensions=['extra', 'codehilite', 'nl2br', 'sane_lists']
            )
        else:
            self.content_html = ''
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or f"Заметка #{self.id}"


class FavoriteFormula(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    formula_text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'formula_text']


class FormulaQuestion(models.Model):
    SUBJECTS = [
        ('physics', 'Физика'),
        ('algebra', 'Алгебра'),
        ('geometry', 'Геометрия'),
    ]
    subject = models.CharField(max_length=20, choices=SUBJECTS, default='physics')
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

    @classmethod
    def get_or_create_general_chats(cls):
        general_chats = [
            {'name': 'Общий чат по физике', 'room_type': 'physics', 'description': 'Обсуждение формул и законов физики'},
            {'name': 'Общий чат по алгебре', 'room_type': 'algebra', 'description': 'Обсуждение алгебраических выражений и уравнений'},
            {'name': 'Общий чат по геометрии', 'room_type': 'geometry', 'description': 'Обсуждение геометрических фигур и теорем'},
        ]
        for chat_data in general_chats:
            cls.objects.get_or_create(
                name=chat_data['name'],
                room_type=chat_data['room_type'],
                defaults={'description': chat_data['description'], 'is_active': True}
            )


class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    _message = models.TextField(db_column='message')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')

    @property
    def message(self):
        return decrypt_message(self._message)

    @message.setter
    def message(self, value):
        self._message = encrypt_message(value)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        try:
            preview = self.message[:30] + '...' if len(self.message) > 30 else self.message
        except:
            preview = '***'
        return f"{self.sender.username}: {preview}"


class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Ожидание'), ('accepted', 'Принята'), ('rejected', 'Отклонена')], default='pending')

    class Meta:
        unique_together = ['from_user', 'to_user']
        ordering = ['-created_at']

    def accept(self):
        if self.status == 'pending':
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


class AIChatHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=20)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'История диалога с AI'
        verbose_name_plural = 'Истории диалогов с AI'


class Formula(models.Model):
    SUBJECTS = [
        ('physics', 'Физика'),
        ('algebra', 'Алгебра'),
        ('geometry', 'Геометрия'),
    ]
    subject = models.CharField(max_length=20, choices=SUBJECTS)
    text = models.CharField("Формула", max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


@receiver(post_migrate)
def create_default_questions(sender, **kwargs):
    if sender.name == 'app':
        if not FormulaQuestion.objects.exists():
            questions_data = [
                # Физика
                ('physics', 'Закон Ома?', 'I = U/R', ['I = U*R', 'I = U/R', 'U = I*R', 'R = U*I']),
                ('physics', 'Формула кинетической энергии?', 'E = mv²/2', ['E = mv', 'E = mv²/2', 'E = mgh', 'E = Fs']),
                ('physics', 'Второй закон Ньютона?', 'F = ma', ['F = mv', 'F = ma', 'F = m/a', 'F = a/m']),
                ('physics', 'Закон всемирного тяготения?', 'F = G·m₁·m₂/r²', ['F = G·m₁·m₂/r', 'F = G·m₁·m₂/r²', 'F = G·r²/m₁·m₂', 'F = m₁·m₂/G·r²']),
                ('physics', 'Первый закон Ньютона?', 'Тело покоится или движется равномерно', ['Тело ускоряется', 'Тело покоится или движется равномерно', 'Тело движется с ускорением', 'На тело действует сила']),
                # Алгебра
                ('algebra', 'Дискриминант квадратного уравнения?', 'D = b² - 4ac', ['D = b² + 4ac', 'D = 4ac - b²', 'D = b² - 4ac', 'D = (b² - 4ac)/2a']),
                ('algebra', 'Квадрат суммы?', '(a+b)² = a² + 2ab + b²', ['(a+b)² = a² + b²', '(a+b)² = a² + 2ab + b²', '(a+b)² = a² - 2ab + b²', '(a+b)² = a² + ab + b²']),
                ('algebra', 'Разность квадратов?', 'a² - b² = (a-b)(a+b)', ['a² - b² = (a+b)²', 'a² - b² = (a-b)²', 'a² - b² = (a-b)(a+b)', 'a² - b² = a² - 2ab + b²']),
                ('algebra', 'Теорема Виета для x²+px+q=0?', 'x₁+x₂ = -p, x₁·x₂ = q', ['x₁+x₂ = p, x₁·x₂ = q', 'x₁+x₂ = -p, x₁·x₂ = -q', 'x₁+x₂ = -p, x₁·x₂ = q', 'x₁+x₂ = p, x₁·x₂ = -q']),
                ('algebra', 'Степень числа aᵐ·aⁿ?', 'a^(m+n)', ['a^(m-n)', 'a^(m+n)', 'a^(m·n)', 'a^(m/n)']),
                # Геометрия
                ('geometry', 'Площадь круга?', 'S = πr²', ['S = 2πr', 'S = πr²', 'S = πd', 'S = πr²/2']),
                ('geometry', 'Теорема Пифагора?', 'c² = a² + b²', ['c = a + b', 'c² = a² - b²', 'c² = a² + b²', 'a² = b² + c²']),
                ('geometry', 'Площадь треугольника?', 'S = ½·a·h', ['S = a·h', 'S = ½·a·h', 'S = a·b', 'S = a·b·sinγ']),
                ('geometry', 'Сумма углов треугольника?', '180°', ['90°', '180°', '360°', '270°']),
                ('geometry', 'Периметр прямоугольника?', 'P = 2(a+b)', ['P = a·b', 'P = 2(a+b)', 'P = a+b', 'P = 4a']),
            ]
            for subject, formula, correct, options in questions_data:
                FormulaQuestion.objects.create(
                    subject=subject,
                    formula=formula,
                    correct_answer=correct,
                    options=options
                )

        if not Formula.objects.exists():
            formulas_data = [
                ('physics', 'E = mc²'),
                ('physics', 'F = ma'),
                ('physics', 'V = IR'),
                ('physics', 'F = G·m₁·m₂/r²'),
                ('algebra', '(a+b)² = a² + 2ab + b²'),
                ('algebra', 'a² - b² = (a-b)(a+b)'),
                ('algebra', 'x₁+x₂ = -b/a'),
                ('algebra', 'D = b² - 4ac'),
                ('geometry', 'S = πr²'),
                ('geometry', 'c² = a² + b²'),
                ('geometry', 'S = ½·a·h'),
                ('geometry', 'P = 2(a+b)'),
                ('geometry', 'Сумма углов треугольника = 180°'),
            ]
            for subject, text in formulas_data:
                Formula.objects.create(subject=subject, text=text)