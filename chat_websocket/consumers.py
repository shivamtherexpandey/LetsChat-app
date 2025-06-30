from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework.authtoken.models import Token
from chat_interface import models
from django.conf import settings
import jwt
from channels.db import database_sync_to_async
from better_profanity import profanity
import json


@database_sync_to_async
def check_token_validity(token):
    """To Validate User Chat Access Token and Provide User, Stored_Chat and Messages Instances Associate to Token."""

    token = models.ChatUserJWT.objects.filter(token=token)

    token_validity = True
    if not token.exists():
        token_validity = False

    user = None
    stored_chat = None
    message = ""
    if token_validity:
        try:
            token = token.first()
            jwt_payload = jwt.decode(
                token.token_jwt, settings.SECRET_KEY, algorithms="HS256"
            )

            user_id = jwt_payload.get("user_id")
            user = models.ChatUser.objects.get(id=user_id)

            Token.objects.get(user=user)

            chat_id = jwt_payload.get("chat_id")
            stored_chat = models.StoredChats.objects.get(id=chat_id)

            messages = stored_chat.chat_messages.order_by("id").values_list(
                "id", "user__id", "user__username", "message"
            )

            delimiter = "_|_|_"

            messages = list(messages)

            if len(messages) >= 10:
                messages = messages[-10::]

            for id, user_id, username, chat in messages:
                message += f"{id}::{user_id}::{username}::{chat}" + delimiter

        except Exception as e:
            token_validity = False
            print(e.args[0])
            message = "Session expire. Restart the chat room."

    return token_validity, user, stored_chat, message[:-5:]


class ChatRoomManager(AsyncWebsocketConsumer):
    async def connect(self):
        # Validate the Session
        token = self.scope["url_route"]["kwargs"]["token"]
        [*responses] = await check_token_validity(token)

        # Handle Invalid Session
        if not responses[0]:
            self.send(text_data=json.dumps({"messages": responses[-1]}))

            await self.close()

        await self.accept()
        self.group_room_name = f"chat_{responses[2].id}"
        await self.channel_layer.group_add(self.group_room_name, self.channel_name)

        self.user_id = responses[1].id
        self.stored_chat_id = responses[2].id

        response = {
            "user_id": responses[1].id,
            "stored_chat_id": responses[2].id,
            "messages": responses[-1],
        }

        await self.send(text_data=json.dumps(response))

    @database_sync_to_async
    def close_chat_session(self, token):
        try:
            models.ChatUserJWT.objects.filter(token=token).delete()
        except:
            pass

    async def disconnect(self, close_code):
        # Leave room group
        token = self.scope["url_route"]["kwargs"]["token"]
        await self.close_chat_session(token)
        await self.channel_layer.group_discard(self.group_room_name, self.channel_name)

    @database_sync_to_async
    def save_chat_message(self, stored_chat, user, message):

        new_chat = models.Chats.objects.create(user=user, message=message)
        stored_chat.chat_messages.add(new_chat)
        new_chat.save()

        delimiter = "_|_|_"
        message = (
            f"{new_chat.id}::{user.id}::{user.username}::{new_chat.message}" + delimiter
        )

        return message[:-5:]

    @database_sync_to_async
    def delete_chat_by_id(self, chat_id, stored_chat):
        models.Chats.objects.get(id=chat_id).delete()

        messages = (
            stored_chat.chat_messages.all()
            .order_by("id")
            .values_list("id", "user__id", "user__username", "message")
        )

        message = ""
        delimiter = "_|_|_"
        for id, user_id, username, msg in messages:
            message += f"{id}::{user_id}::{username}::{msg}" + delimiter

        return message[:-5:]

    async def receive(self, text_data):
        # Validate the Session
        token = self.scope["url_route"]["kwargs"]["token"]
        [*responses] = await check_token_validity(token)

        # Handle Invalid Session
        if not responses[0]:
            self.send(text_data=json.dumps({"messages": responses[-1]}))
            await self.close()

        text_data_json = json.loads(text_data)
        operation = text_data_json.get("operation")
        message = text_data_json["message"]

        # Censor Words
        profanity.load_censor_words()

        censored_message = profanity.censor(message)

        message = censored_message

        if operation:
            """If delete message operation has to be performed."""
            user_id = responses[1].id
            request_user_id = text_data_json.get("user_id")

            if user_id == request_user_id:
                chat_id = text_data_json.get("chat_id")
                message = await self.delete_chat_by_id(chat_id, responses[2])

                await self.channel_layer.group_send(
                    self.group_room_name,
                    {
                        "type": "chat.message",
                        "messages": message,
                        "operation": operation,
                    },
                )
            else:
                self.close()

        else:
            message = await self.save_chat_message(responses[2], responses[1], message)

            await self.channel_layer.group_send(
                self.group_room_name, {"type": "chat.message", "messages": message}
            )

    async def chat_message(self, event):
        message = event["messages"]
        operation = event.get("operation")

        response = {
            "user_id": self.user_id,
            "stored_chat_id": self.stored_chat_id,
            "messages": message,
        }

        if operation:
            response["operation"] = operation

        # Send message to WebSocket
        await self.send(text_data=json.dumps(response))
