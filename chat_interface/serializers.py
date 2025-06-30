from rest_framework import serializers
from chat_interface import models
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.models import Token


class SignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ChatUser
        fields = ["username", "password", "contact"]

    def validate_contact(self, value):

        if not value or any([not digit.isdigit() for digit in value]):
            raise ValidationError("Invalid contact field.")

        if len(value) < 8:
            raise ValidationError("Invalid length of contact.")

        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        validated_data.pop("saved_contact", None)
        instance = self.Meta.model(**validated_data)

        if password:
            instance.set_password(password)

        instance.save()

        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data.pop("password", None)
        return data


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if username and password:
            try:
                user = models.ChatUser.objects.get(username=username)
            except models.ChatUser.DoesNotExist:
                msg = "Unable to log in with provided credentials."
                raise serializers.ValidationError(msg, code="authorization")

            if not user.check_password(password):
                msg = "Unable to log in with provided credentials."
                raise serializers.ValidationError(msg, code="authorization")

            token, _ = Token.objects.get_or_create(user=user)
            attrs["token"] = token

        else:
            msg = 'Must include "username" and "password".'
            raise serializers.ValidationError(msg, code="authorization")

        return attrs


class ChatUserContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ChatUser
        fields = ["username", "contact"]


class ChatUserSavedContactSerializer(serializers.ModelSerializer):
    saved_contact = ChatUserContactSerializer(many=True)

    class Meta:
        model = models.ChatUser
        fields = ["saved_contact"]


class ContactSerilizer(serializers.Serializer):
    contact = serializers.CharField(max_length=15)

    def validate_contact(self, value):

        if not value or any([not digit.isdigit() for digit in value]):
            raise ValidationError("Invalid contact field.")

        try:
            user = models.ChatUser.objects.get(contact=value)
        except models.ChatUser.DoesNotExist as e:
            raise serializers.ValidationError("invalid contact.")

        return user
