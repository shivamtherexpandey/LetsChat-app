from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.models import Token


class TokenAuthentication(BaseAuthentication):

    def authenticate(self, request):
        auth_header = request.headers.get("token")
        if not auth_header:
            return None

        try:
            key = auth_header
            token = Token.objects.get(key=key)
        except Token.DoesNotExist:
            raise AuthenticationFailed("Invalid token")

        return (token.user, token)
