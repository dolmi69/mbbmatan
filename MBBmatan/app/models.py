from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

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