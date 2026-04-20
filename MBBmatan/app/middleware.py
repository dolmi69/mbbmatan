from django.utils.deprecation import MiddlewareMixin
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
import random


ERROR_MESSAGES = {
    400: 'Некорректный запрос.',
    403: 'Доступ запрещён. У вас нет прав для просмотра этой страницы.',
    404: 'Страница не найдена. Возможно, её удалили или вы ошиблись в адресе.',
    500: 'Внутренняя ошибка сервера. Мы уже работаем над исправлением.',
}


def render_error(request, code, message=None):
    context = {
        'error_code': code,
        'message': message or ERROR_MESSAGES.get(code, 'Произошла ошибка.'),
    }
    return render(request, 'error.html', context, status=code)


class ErrorPageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, Http404):
            return render_error(request, 404, str(exception) or None)
        if isinstance(exception, PermissionDenied):
            return render_error(request, 403, str(exception) or None)
        return None


class MascotMiddleware(MiddlewareMixin):

    def process_template_response(self, request, response):
        if hasattr(response, 'context_data'):
            context = response.context_data or {}

            mascot = self.get_mascot_for_context(request, context)

            if mascot:
                context['mascot_template'] = f'mascot/{mascot}.html'
                response.context_data = context

        return response

    def get_mascot_for_context(self, request, context):
        from django.contrib import messages

        storage = messages.get_messages(request)
        for message in storage:
            if message.tags == 'success':
                return 'thumbs_up'

        path = request.path

        if '/quiz/result/' in path:
            score = context.get('score', 0)
            total = context.get('total', 1)
            percentage = (score / total * 100) if total > 0 else 0

            if percentage >= 80:
                return 'thumbs_up'
            elif percentage >= 50:
                return 'neutral'
            else:
                return 'wrong'

        elif '/profile' in path:
            attempts = context.get('attempts', [])
            if attempts:
                last_attempt = attempts[0] if attempts else None
                if last_attempt and last_attempt.success_percent() >= 70:
                    return 'thumbs_up'

        elif '/quiz/' in path and 'result' not in path:
            current_number = context.get('current_number', 1)
            total_questions = context.get('total_questions', 5)

            if current_number == total_questions:
                return 'neutral'

        elif hasattr(response, 'status_code') and response.status_code >= 400:
            return 'wrong'

        return 'neutral'


def mascot_context(request):
    mascot_states = {
        'neutral': 'Нейтральное состояние',
        'thumbs_up': 'Отличная работа!',
        'wrong': 'Нужно подтянуть знания...'
    }

    mascot_state = 'neutral'

    if request.user.is_authenticated:
        from .models import TestAttempt
        attempts = TestAttempt.objects.filter(user=request.user).order_by('-date')[:1]
        if attempts:
            last_attempt = attempts[0]
            if last_attempt.success_percent() >= 80:
                mascot_state = 'thumbs_up'
            elif last_attempt.success_percent() < 50:
                mascot_state = 'wrong'

    return {
        'mascot_state': mascot_state,
        'mascot_message': mascot_states.get(mascot_state, ''),
        'show_mascot': True
    }