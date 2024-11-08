from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone
from datetime import timedelta

class ExpiringTokenAuthentication(TokenAuthentication):
    """
    Token Authentication com expiração
    """
    def authenticate_credentials(self, key):
        try:
            token = Token.objects.get(key=key)
        except Token.DoesNotExist:
            raise AuthenticationFailed('Token inválido')

        if not token.user.is_active:
            raise AuthenticationFailed('Usuário inativo ou excluído')

        # Verifica expiração (30 dias)
        utc_now = timezone.now()
        if token.created < utc_now - timedelta(days=30):
            token.delete()
            raise AuthenticationFailed('Token expirado')

        return (token.user, token) 