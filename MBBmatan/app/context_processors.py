from .models import Notification

def user_profile(request):
    if request.user.is_authenticated:
        return {'user_profile': request.user.profile}
    return {}

def mascot_context(request):
    mascot_states = {
        'neutral': 'Нейтральное состояние',
        'thumbs_up': 'Отличная работа!',
        'wrong': 'Нужно подтянуть знания...'
    }
    mascot_state = 'neutral'
    mascot_message = 'Продолжайте обучение!'
    unread_notifications = 0

    if request.user.is_authenticated:
        profile = request.user.profile
        success_rate = profile.success_rate()
        if success_rate >= 70:
            mascot_state = 'thumbs_up'
            mascot_message = 'Отличные результаты!'
        elif success_rate >= 40:
            mascot_state = 'neutral'
            mascot_message = 'Продолжайте в том же духе!'
        else:
            mascot_state = 'wrong'
            mascot_message = 'Есть над чем поработать!'
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    return {
        'global_mascot_state': mascot_state,
        'global_mascot_message': mascot_message,
        'user_level': profile.level if request.user.is_authenticated else None,
        'user_tests_completed': profile.tests_completed if request.user.is_authenticated else None,
        'unread_notifications': unread_notifications,
        'mascot_state': mascot_state,
        'mascot_message': mascot_message,
    }