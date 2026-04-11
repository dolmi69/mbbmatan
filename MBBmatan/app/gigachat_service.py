import uuid
from gigachat import GigaChat
from django.conf import settings
from .models import AIChatHistory

class GigaChatService:
    def __init__(self, user, session_id=None):
        self.user = user
        self.session_id = session_id or str(uuid.uuid4())
        self.client = GigaChat(
            credentials=settings.GIGACHAT_CREDENTIALS,
            verify_ssl_certs=settings.GIGACHAT_VERIFY_SSL,
            model=settings.GIGACHAT_MODEL
        )

    def get_history(self, limit=10):
        history = AIChatHistory.objects.filter(
            user=self.user,
            session_id=self.session_id
        ).order_by('-created_at')[:limit]
        return list(history)[::-1]

    def send_message(self, message):
        user_msg = AIChatHistory.objects.create(
            user=self.user,
            session_id=self.session_id,
            role='user',
            content=message
        )

        history = self.get_history()
        messages = [{"role": msg.role, "content": msg.content} for msg in history]

        try:
            response = self.client.chat({
                "model": settings.GIGACHAT_MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000
            })
            assistant_message = response.choices[0].message.content

            AIChatHistory.objects.create(
                user=self.user,
                session_id=self.session_id,
                role='assistant',
                content=assistant_message
            )

            return {
                'success': True,
                'message': assistant_message,
                'session_id': self.session_id
            }
        except Exception as e:
            user_msg.delete()
            return {
                'success': False,
                'error': str(e)
            }

    def clear_history(self):
        AIChatHistory.objects.filter(
            user=self.user,
            session_id=self.session_id
        ).delete()
        return {'success': True}