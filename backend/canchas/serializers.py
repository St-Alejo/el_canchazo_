from rest_framework import serializers

from .models import Cancha, FotoCancha, HorarioDisponible


class FotoCanchaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FotoCancha
        fields = ["id", "imagen", "orden"]


class CanchaListSerializer(serializers.ModelSerializer):
    deporte = serializers.CharField(source="deporte.nombre", read_only=True)
    precio_desde = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, allow_null=True)

    class Meta:
        model = Cancha
        fields = ["id", "nombre", "direccion", "latitud", "longitud", "deporte", "servicios", "precio_desde"]


class CanchaDetailSerializer(CanchaListSerializer):
    fotos = FotoCanchaSerializer(many=True, read_only=True)

    class Meta(CanchaListSerializer.Meta):
        fields = CanchaListSerializer.Meta.fields + ["descripcion", "telefono", "fotos"]


class HorarioDisponibleSerializer(serializers.ModelSerializer):
    class Meta:
        model = HorarioDisponible
        fields = ["id", "hora_inicio", "hora_fin", "tarifa"]


class FiltroCanchaSerializer(serializers.Serializer):
    deporte = serializers.IntegerField(required=False)
    ubicacion = serializers.CharField(required=False, allow_blank=True)
    precio_min = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    precio_max = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    servicios = serializers.CharField(required=False, allow_blank=True, help_text="Separados por coma")

    def to_filtros(self):
        datos = self.validated_data
        servicios_csv = datos.get("servicios")
        return {
            "deporte": datos.get("deporte"),
            "ubicacion": datos.get("ubicacion"),
            "precio_min": datos.get("precio_min"),
            "precio_max": datos.get("precio_max"),
            "servicios": [s.strip() for s in servicios_csv.split(",") if s.strip()] if servicios_csv else None,
        }


class DisponibilidadQuerySerializer(serializers.Serializer):
    fecha = serializers.DateField()
