from django.contrib import admin
from .models import (
    Note,
    FavoriteFormula,
    FormulaQuestion,
    TestAttempt,
    UserProfile,
    ChatRoom,
    ChatMessage,
)

admin.site.register(Note)
admin.site.register(FavoriteFormula)
admin.site.register(TestAttempt)


@admin.register(FormulaQuestion)
class FormulaQuestionAdmin(admin.ModelAdmin):
    list_display = ['formula', 'correct_answer', 'created_at']
    search_fields = ['formula']
    list_filter = ['created_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'level', 'experience', 'points', 'total_questions_answered']
    list_filter = ['level']
    search_fields = ['user__username']


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'room_type', 'created_by', 'created_at']
    list_filter = ['room_type', 'is_active']
    search_fields = ['name', 'description']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'room', 'timestamp', 'is_read']
    list_filter = ['timestamp', 'is_read']
    search_fields = ['message', 'sender__username']

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-timestamp')[:1000]