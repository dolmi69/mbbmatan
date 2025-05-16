from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver


User = get_user_model()


# Модель для хранения формул
class Formulas(models.Model):
    content = models.CharField(max_length=255)  # Сама формула
    topic = models.CharField(max_length=100)    # Тема, к которой относится формула
    description = models.TextField(blank=True, null=True)  # Описание формулы



# Модель для хранения теории
class Theory(models.Model):
    content = models.TextField()  # Теоретический материал
    topic = models.CharField(max_length=100)  # Тема, к которой относится теория



# Модель для избранных формул пользователя
class FavFormulas(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Связь с пользователем
    formula = models.ForeignKey(Formulas, on_delete=models.CASCADE)  # Связь с формулой

    class Meta:
        unique_together = ('user', 'formula')  # Уникальность пары пользователь-формула

    def __str__(self):
        return f"{self.user.username} - {self.formula.topic}"






class Note(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class FavoriteFormula(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    formula_text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.formula_text}"


class FormulaQuestion(models.Model):
    formula = models.CharField("Вопрос", max_length=200)
    correct_answer = models.CharField("Правильный ответ", max_length=200)
    options = models.JSONField("Варианты ответов", default=list)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    def __str__(self):
        return self.formula


@receiver(post_migrate)
def create_initial_questions(sender, **kwargs):
    if sender.name == 'app':
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
                "formula": "Формула для расчета скорости:",
                "correct_answer": "v = s/t",
                "options": ["F = m·a", "P = F/S", "v = s/t", "Q = I·t"]
            },
            {
                "formula": "Что измеряют в Паскалях?",
                "correct_answer": "Давление",
                "options": ["Силу", "Давление", "Скорость", "Энергию"]
            },
            {
                "formula": "Пример простого механизма:",
                "correct_answer": "Рычаг",
                "options": ["Динамометр", "Амперметр", "Рычаг", "Манометр"]
            }
        ]

        for q in initial_questions:
            if not FormulaQuestion.objects.filter(formula=q['formula']).exists():
                FormulaQuestion.objects.create(
                    formula=q['formula'],
                    correct_answer=q['correct_answer'],
                    options=q['options']
                )

class TestAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    correct_answers = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)

    def success_percent(self):
        if self.total_questions == 0:
            return 0
        return round((self.correct_answers / self.total_questions) * 100, 2)

    def clean(self):
        if self.total_questions < 0:
            raise ValidationError("Total questions cannot be negative.")
        if self.correct_answers < 0:
            raise ValidationError("Correct answers cannot be negative.")

class TestAnswer(models.Model):
    text = models.TextField()
    image = models.ImageField(default=None, null=True, blank=True)
    right = models.BooleanField()

class TestData(models.Model):
    class TypeChoices(models.TextChoices):
        many = "many", "many"
        input = "input", "input"
    text = models.TextField()
    image = models.ImageField(default=None, null=True, blank=True)
    type = models.CharField(choices=TypeChoices.choices,max_length=200, default="many")
    choices_count = models.IntegerField(default=1)
    answers = models.ForeignKey(to=TestAnswer, on_delete=models.CASCADE, related_name="test")


class UserAnswer(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="answers")
    answer = models.ForeignKey(to=TestAnswer, on_delete=models.CASCADE, related_name="users")
    date = models.DateTimeField(auto_now_add=True)


