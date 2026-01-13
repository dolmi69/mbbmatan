from django.utils.deprecation import MiddlewareMixin
import random


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