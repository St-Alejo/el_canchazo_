from django.utils import timezone

from .models import Usuario


def registrar_usuario(datos_validados):
    """Crea un Usuario con contraseña hasheada y registra el consentimiento de datos (Ley 1581)."""
    datos = dict(datos_validados)
    password = datos.pop("password")
    consentimiento_aceptado = datos.pop("consentimiento_datos_aceptado")

    usuario = Usuario(**datos)
    usuario.consentimiento_datos_aceptado = consentimiento_aceptado
    usuario.fecha_consentimiento = timezone.now()
    usuario.set_password(password)
    usuario.save()
    return usuario
