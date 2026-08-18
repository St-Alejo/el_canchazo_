from rest_framework import serializers

from .models import Calificacion, Reserva


class CalificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calificacion
        fields = ["id", "calificado_por", "puntuacion", "comentario", "fecha"]
        read_only_fields = fields


class ReservaSerializer(serializers.ModelSerializer):
    cancha_nombre = serializers.CharField(source="cancha.nombre", read_only=True)
    calificaciones = CalificacionSerializer(many=True, read_only=True)

    class Meta:
        model = Reserva
        fields = [
            "id",
            "cancha",
            "cancha_nombre",
            "usuario",
            "fecha",
            "hora_inicio",
            "hora_fin",
            "estado",
            "asistencia",
            "monto_anticipo",
            "monto_tarifa_servicio",
            "fecha_creacion",
            "calificaciones",
        ]
        read_only_fields = fields


class CrearReservaSerializer(serializers.Serializer):
    cancha_id = serializers.IntegerField()
    fecha = serializers.DateField()
    hora_inicio = serializers.TimeField()
    redirect_url = serializers.URLField()


class MarcarAsistenciaSerializer(serializers.Serializer):
    asistencia = serializers.ChoiceField(choices=Reserva.ASISTENCIA_CHOICES)


class CalificarReservaSerializer(serializers.Serializer):
    puntuacion = serializers.IntegerField(min_value=1, max_value=5)
    comentario = serializers.CharField(required=False, allow_blank=True, default="")
