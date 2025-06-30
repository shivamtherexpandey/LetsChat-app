from django.urls import re_path
from chat_websocket import consumers

websocket_urlpatterns = [
    re_path(r"^ws/chat/(?P<token>[-\w]+)/$", consumers.ChatRoomManager.as_asgi()),
]
