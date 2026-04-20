import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatMessage
from .banwords import censor

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 2000


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close(code=4001)
            return

        allowed = await self._user_has_access()
        if not allowed:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except (ValueError, TypeError):
            await self._send_error('Некорректный формат сообщения')
            return

        raw_message = (data.get('message') or '').strip()
        if not raw_message:
            return
        if len(raw_message) > MAX_MESSAGE_LENGTH:
            raw_message = raw_message[:MAX_MESSAGE_LENGTH]

        message_text = censor(raw_message)
        reply_to_id = data.get('reply_to')
        if reply_to_id is not None:
            try:
                reply_to_id = int(reply_to_id)
            except (ValueError, TypeError):
                reply_to_id = None

        if not await self._user_has_access():
            await self._send_error('Нет доступа к чату')
            return

        try:
            message = await self._save_message(message_text, reply_to_id)
        except Exception:
            logger.exception('Не удалось сохранить сообщение')
            await self._send_error('Не удалось отправить сообщение')
            return

        reply_payload = None
        if message.reply_to_id:
            reply_payload = {
                'id': message.reply_to.id,
                'sender': message.reply_to.sender.username,
                'sender_id': message.reply_to.sender_id,
                'message': message.reply_to.message,
            }

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'sender': self.user.username,
                    'sender_id': self.user.id,
                    'message': message.message,
                    'timestamp': message.timestamp.strftime('%H:%M'),
                    'reply_to': reply_payload,
                }
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    async def _send_error(self, text):
        await self.send(text_data=json.dumps({'error': text}))

    @database_sync_to_async
    def _user_has_access(self):
        try:
            room = ChatRoom.objects.get(id=self.room_id, is_active=True)
        except ChatRoom.DoesNotExist:
            return False
        if room.room_type in ('physics', 'algebra', 'geometry'):
            return True
        return room.participants.filter(pk=self.user.pk).exists()

    @database_sync_to_async
    def _save_message(self, message_text, reply_to_id):
        room = ChatRoom.objects.get(id=self.room_id)
        reply_to = None
        if reply_to_id:
            reply_to = ChatMessage.objects.filter(id=reply_to_id, room=room).select_related('sender').first()
        msg = ChatMessage.objects.create(
            room=room,
            sender=self.user,
            message=message_text,
            reply_to=reply_to,
        )
        if reply_to is not None:
            msg.reply_to = reply_to
        return msg
