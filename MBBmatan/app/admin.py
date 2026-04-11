from django.contrib import admin
from .models import (
    Note, FavoriteFormula, FormulaQuestion, TestAttempt, UserProfile,
    ChatRoom, ChatMessage, Notification
)
from django.utils.html import format_html


@admin.register(FormulaQuestion)
class FormulaQuestionAdmin(admin.ModelAdmin):
    list_display = ['formula', 'correct_answer', 'options_preview', 'created_at']
    search_fields = ['formula', 'correct_answer']
    list_filter = ['created_at']

    def options_preview(self, obj):
        return ', '.join(obj.options)

    options_preview.short_description = 'Варианты ответов'


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'correct_answers', 'total_questions', 'success_percent']
    list_filter = ['date', 'user']
    readonly_fields = ['user', 'date', 'correct_answers', 'total_questions']

    def success_percent(self, obj):
        return f"{obj.success_percent()}%"

    success_percent.short_description = 'Успешность'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'text', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    actions = ['mark_as_read', 'send_system_notification']

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    mark_as_read.short_description = "Отметить как прочитанные"

    def send_system_notification(self, request, queryset):
        # Действие для рассылки уведомлений (можно доработать)
        pass

    send_system_notification.short_description = "Отправить системное уведомление выбранным пользователям"