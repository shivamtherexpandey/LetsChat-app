from django.contrib import admin
from chat_interface import models


class ChatUserAdmin(admin.ModelAdmin):
    exclude = ("password",)


# Register your models here.
admin.site.register(models.ChatUser, ChatUserAdmin)
admin.site.register(models.StoredChats)
admin.site.register(models.ChatUserJWT)
admin.site.register(models.Chats)
