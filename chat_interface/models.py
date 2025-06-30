from typing import Iterable
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from chat_interface.manager import ChatUserManager
from django.contrib.auth.tokens import default_token_generator
from django.core.validators import MinLengthValidator
import jwt
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
import secrets


class ChatUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        max_length=150, unique=True, validators=[MinLengthValidator(4)]
    )
    contact = models.CharField(
        max_length=15, unique=True, validators=[MinLengthValidator(8)]
    )
    saved_contact = models.ManyToManyField("self", blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = ChatUserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["contact"]

    def __str__(self):
        return self.username


class ChatUserJWT(models.Model):

    token = models.CharField(max_length=100)
    token_jwt = models.CharField(max_length=255)

    def save(self, *args, **kwargs):

        if not self.token:
            self.token = secrets.token_urlsafe(16)

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.token


class StoredChats(models.Model):

    user1 = models.ForeignKey(
        ChatUser, related_name="chats_as_user1", on_delete=models.PROTECT
    )
    user2 = models.ForeignKey(
        ChatUser, related_name="chats_as_user2", on_delete=models.PROTECT
    )
    chat_messages = models.ManyToManyField("Chats", blank=True)

    def generate_jwt_token(self, user_id):
        payload = {
            "chat_id": self.id,
            "user_id": user_id,
            "exp": timezone.now() + timedelta(hours=1),
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        return token

    def __str__(self) -> str:
        return f"Chat-{self.user1}-{self.user2}"


class Chats(models.Model):
    user = models.ForeignKey(ChatUser, on_delete=models.PROTECT)
    message = models.TextField()

    def __str__(self) -> str:
        return f"{self.user.id}__{self.user.username}||{self.message}"
