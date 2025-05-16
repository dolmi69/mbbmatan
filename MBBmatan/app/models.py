from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.signals import post_migrate
from django.dispatch import receiver

User = get_user_model()

class Formulas(models.Model):
    content = models.CharField(max_length=255)
    topic = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

class Theory(models.Model):
    content = models.TextField()
    topic = models.CharField(max_length=100)

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

class FormulaQuestion(models.Model):
    formula = models.CharField("Вопрос", max_length=200)
    correct_answer = models.CharField("Правильный ответ", max_length=200)
    options = models.JSONField("Варианты ответов", default=list)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    def __str__(self):
        return self.formula

class TestAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    correct_answers = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)

    def success_percent(self):
        return round((self.correct_answers / self.total_questions) * 100, 2) if self.total_questions > 0 else 0

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
            },
            {
                "formula": "Формула расчета давления:",
                "correct_answer": "P = F/S",
                "options": ["P = m/V", "P = F/S", "E = mc²", "v = a·t"]
            },
            {
                "formula": "Единица измерения работы:",
                "correct_answer": "Джоуль",
                "options": ["Ньютон", "Паскаль", "Джоуль", "Ватт"]
            },
            {
                "formula": "Что характеризует инерция тела?",
                "correct_answer": "Способность сохранять скорость",
                "options": ["Способность совершать работу", "Способность сохранять скорость", "Массу тела", "Энергию тела"]
            },
            {
                "formula": "Формула механической работы:",
                "correct_answer": "A = F·s",
                "options": ["A = m·g·h", "A = F·s", "A = P·t", "A = I·U"]
            },
            {
                "formula": "Устройство для измерения силы:",
                "correct_answer": "Динамометр",
                "options": ["Барометр", "Амперметр", "Динамометр", "Манометр"]
            },
            {
                "formula": "Закон Ома для участка цепи:",
                "correct_answer": "I = U/R",
                "options": ["I = U/R", "Q = I·t", "P = I²·R", "U = A/q"]
            },
            {
                "formula": "Формула кинетической энергии:",
                "correct_answer": "E = mv²/2",
                "options": ["E = mgh", "E = mv²/2", "E = kx²/2", "E = Q/Δt"]
            },
            {
                "formula": "Единица измерения мощности:",
                "correct_answer": "Ватт",
                "options": ["Джоуль", "Вольт", "Ампер", "Ватт"]
            },
            {
                "formula": "Формула потенциальной энергии:",
                "correct_answer": "E = mgh",
                "options": ["E = mv²/2", "E = kx²/2", "E = mgh", "E = Q/Δt"]
            },
            {
                "formula": "Первый закон термодинамики:",
                "correct_answer": "Q = ΔU + A",
                "options": ["Q = cmΔT", "Q = ΔU + A", "A = N·t", "P = ρgh"]
            }
        ]

        for q in initial_questions:
            FormulaQuestion.objects.get_or_create(
                formula=q['formula'],
                defaults={
                    'correct_answer': q['correct_answer'],
                    'options': q['options']
                }
            )