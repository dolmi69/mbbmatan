def user_profile(request):
    if request.user.is_authenticated:
        return {
            'user_profile': request.user.profile
        }
    return {}


def mascot_context(request):
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

        return {
            'global_mascot_state': mascot_state,
            'global_mascot_message': mascot_message,
            'user_level': profile.level,
            'user_tests_completed': profile.tests_completed,
        }

    return {}