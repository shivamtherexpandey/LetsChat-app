from django.urls import path
from chat_interface import views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path("letschat/signup", views.SignupPage.as_view(), name="signup_page"),
    path("letschat/login", views.LoginPage.as_view(), name="login_page"),
    path("letschat/home", views.Dashboard.as_view(), name="home_page"),
    path(
        "letschat/manage/contacts", views.ManageContacts.as_view(), name="contacts_page"
    ),
    path("letschat/manage/chats", views.ManageChats.as_view(), name="chats_page"),
    path("letschat/chat/<slug:token>", views.ChatRoom.as_view(), name="chatroom_page"),
    path("api/letschat/signup", views.UserSignup.as_view(), name="signup_api"),
    path("api/letschat/login", obtain_auth_token, name="login_api"),
    path("api/letschat/me", views.UserData.as_view(), name="me_api"),
    path("api/letschat/logout", views.UserLogout.as_view(), name="logout_api"),
    path(
        "api/letschat/contacts",
        views.ListCreateRemoveContacts.as_view(),
        name="contacts_api",
    ),
    path("api/letschat/show-users", views.ListUser.as_view(), name="show_users_api"),
    path("api/letschat/start-chat", views.StartChat.as_view(), name="start_chat_api"),
]
