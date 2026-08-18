from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import Usuario


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    consentimiento_datos_aceptado = serializers.BooleanField()

    class Meta:
        model = Usuario
        fields = [
            "username",
            "email",
            "celular",
            "password",
            "rol",
            "consentimiento_datos_aceptado",
        ]

    def validate_rol(self, valor):
        if valor not in (Usuario.ROL_JUGADOR, Usuario.ROL_ADMIN_CANCHA):
            raise serializers.ValidationError("Rol no permitido en el autoregistro.")
        return valor

    def validate_consentimiento_datos_aceptado(self, valor):
        if not valor:
            raise serializers.ValidationError(
                "Debes aceptar el tratamiento de datos personales (Ley 1581) para registrarte."
            )
        return valor


class LoginSerializer(serializers.Serializer):
    identificador = serializers.CharField(help_text="Celular o correo")
    password = serializers.CharField(write_only=True)

    def validate(self, datos):
        usuario = authenticate(
            self.context["request"],
            username=datos["identificador"],
            password=datos["password"],
        )
        if usuario is None:
            raise serializers.ValidationError("Credenciales inválidas.")
        datos["usuario"] = usuario
        return datos


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "username", "email", "celular", "rol"]
        read_only_fields = fields
