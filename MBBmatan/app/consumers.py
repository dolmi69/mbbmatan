import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatMessage

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        room = await database_sync_to_async(ChatRoom.objects.get)(id=self.room_id)
        participants = await database_sync_to_async(list)(room.participants.all())
        if self.user not in participants:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_text = data['message']
        reply_to_id = data.get('reply_to')

        message = await self.save_message(message_text, reply_to_id)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'sender': self.user.username,
                    'message': message.message,
                    'timestamp': message.timestamp.strftime('%H:%M'),
                    'reply_to': {
                        'id': message.reply_to.id,
                        'sender': message.reply_to.sender.username,
                        'message': message.reply_to.message
                    } if message.reply_to else None
                }
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    @database_sync_to_async
    def save_message(self, message_text, reply_to_id):
        room = ChatRoom.objects.get(id=self.room_id)
        reply_to = None
        if reply_to_id:
            try:
                reply_to = ChatMessage.objects.get(id=reply_to_id)
            except ChatMessage.DoesNotExist:
                pass
        return ChatMessage.objects.create(
            room=room,
            sender=self.user,
            message=message_text,
            reply_to=reply_to
        )