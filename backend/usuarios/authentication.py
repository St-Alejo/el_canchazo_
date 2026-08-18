from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from .models import Usuario


class CelularOCorreoBackend(ModelBackend):
    """Permite iniciar sesión con el celular o el correo como identificador."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        try:
            usuario = Usuario.objects.get(Q(celular=username) | Q(email__iexact=username))
        except (Usuario.DoesNotExist, Usuario.MultipleObjectsReturned):
            return None
        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None
