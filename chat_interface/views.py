from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import generics
from chat_interface import models, serializers, authentication
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework import status
from django.views import View
from django.db.models import Q
from django.forms.models import model_to_dict
from django.conf import settings
from rest_framework.filters import SearchFilter
import jwt


class UserSignup(generics.CreateAPIView):
    queryset = models.ChatUser.objects.all()
    serializer_class = serializers.SignUpSerializer


class UserData(generics.GenericAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):

        user = request.user

        serializer = serializers.ChatUserContactSerializer(instance=user, many=False)

        return Response(serializer.data, status=status.HTTP_200_OK)


class UserLogout(generics.DestroyAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Token.objects.all()

    def delete(self, request, *args, **kwargs):
        try:
            token = request.auth
            token.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except:
            return Response(
                {"error": "Failed to logout"}, status=status.HTTP_400_BAD_REQUEST
            )


class ListCreateRemoveContacts(generics.ListCreateAPIView, generics.DestroyAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = models.ChatUser.objects.all()
    serializer_class = serializers.ChatUserContactSerializer

    def get(self, request):

        serializer = serializers.ChatUserSavedContactSerializer(instance=request.user)

        return Response(
            {
                "results": serializer.data,
            }
        )

    def post(self, request):
        serializer = serializers.ContactSerilizer(data=request.data)
        serializer.is_valid()
        user_contact = serializer.validated_data.get("contact")

        if user_contact.id == request.user.id:
            raise PermissionDenied("not allowed.")

        request.user.saved_contact.add(user_contact)

        return Response(
            {
                "message": f"{user_contact} with contact {user_contact.contact} has has been added"
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        serializer = serializers.ContactSerilizer(data=request.data)
        serializer.is_valid()
        user_contact = serializer.validated_data.get("contact")

        if user_contact.id == request.user.id:
            raise PermissionDenied("not allowed.")

        if not request.user.saved_contact.filter(id=user_contact.id).exists():
            raise NotFound("user with contact was not in the saved contact list.")

        request.user.saved_contact.remove(user_contact)

        return Response(
            {"message": "user has been removed from the list."},
            status=status.HTTP_200_OK,
        )


class ListUser(generics.ListAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ChatUserContactSerializer
    filter_backends = [SearchFilter]
    search_fields = ["username"]

    def get_queryset(self):
        return (
            models.ChatUser.objects.filter(is_superuser=False)
            .exclude(id=self.request.user.id)
            .exclude(
                username__in=self.request.user.saved_contact.values_list(
                    "username", flat=True
                )
            )
        )


class StartChat(generics.GenericAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = serializers.ContactSerilizer(data=request.data)
        serializer.is_valid()
        user_contact = serializer.validated_data.get("contact")

        if user_contact.id == request.user.id:
            raise PermissionDenied("not allowed.")

        user1 = request.user
        user2 = user_contact

        if not user1.saved_contact.filter(id=user2.id).exists():
            raise PermissionDenied(
                "user contact is not part of saved contacts. Kindly add the user contact."
            )

        chat_exists = models.StoredChats.objects.filter(
            Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1)
        )

        if chat_exists.exists():
            chat_exists = chat_exists.first()

        else:
            chat_exists = models.StoredChats.objects.create(user1=user1, user2=user2)
            chat_exists.save()

        token = chat_exists.generate_jwt_token(user1.id)

        jwt_to_token = models.ChatUserJWT.objects.create(token_jwt=token)

        path = f"letschat/chat/{jwt_to_token.token}"

        full_path_chat = f"/{path}"

        return Response(
            {
                "location": full_path_chat,
            },
            status=status.HTTP_201_CREATED,
        )


class SignupPage(View):

    def get(self, request, *args, **kwargs):

        return render(request, "signup.html")


class LoginPage(View):

    def get(self, request, *args, **kwargs):

        return render(request, "login.html")


class Dashboard(View):

    def get(self, request, *args, **kwargs):

        return render(request, "home.html")


class ManageContacts(View):

    def get(self, request, *args, **kwargs):

        return render(request, "contacts.html")


class ManageChats(View):

    def get(self, request, *args, **kwargs):

        return render(request, "chats.html")


class ChatRoom(View):

    def get(self, request, *args, **kwargs):
        token = kwargs.get("token")

        jwt_token = models.ChatUserJWT.objects.filter(token=token)

        if not jwt_token.exists():
            return HttpResponse("Session Closed. Restart the Session.")

        jwt_token = jwt_token.first()

        try:
            jwt_payload = jwt.decode(
                jwt_token.token_jwt, settings.SECRET_KEY, algorithms="HS256"
            )

            user_id = jwt_payload.get("user_id")

            user = models.ChatUser.objects.get(id=user_id)

        except Exception as e:
            print(e.args[0])
            jwt_token.delete()
            return HttpResponse("Session expired. Please restart the chat room.")

        chat = models.StoredChats.objects.get(id=jwt_payload.get("chat_id"))

        # print(chat)

        context = {
            "chat": model_to_dict(chat),
            "token": token,
            "receiver": (
                chat.user1.username if user.id == chat.user2.id else chat.user2.username
            ),
        }
        return render(request, "chatroom.html", context)
