from django.contrib.auth.models import BaseUserManager


class ChatUserManager(BaseUserManager):

    def create_user(self, username, contact, password=None):
        if not username:
            raise ValueError("The Username field must be set")
        if not contact:
            raise ValueError("The Contact field must be set")

        user = self.model(username=username, contact=contact)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, contact, password=None):
        user = self.create_user(username, contact, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
