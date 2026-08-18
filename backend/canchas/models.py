from django.conf import settings
from django.db import models


class Deporte(models.Model):
    nombre = models.CharField(max_length=50)  # "Futbol", "Tenis", "Bolos"

    def __str__(self):
        return self.nombre


class Cancha(models.Model):
    ESTADO_PENDIENTE = "pendiente"
    ESTADO_APTO = "apto"
    ESTADO_NO_APTO = "no_apto"
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_APTO, "Apto"),
        (ESTADO_NO_APTO, "No apto"),
    ]

    nombre = models.CharField(max_length=150)
    descripcion = models.TextField()
    direccion = models.CharField(max_length=255)
    latitud = models.FloatField()
    longitud = models.FloatField()
    telefono = models.CharField(max_length=20)
    deporte = models.ForeignKey(Deporte, on_delete=models.PROTECT)
    servicios = models.JSONField(default=list)  # ["parqueadero", "cubierta", "baño"]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE)
    administrador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class FotoCancha(models.Model):
    cancha = models.ForeignKey(Cancha, related_name="fotos", on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to="canchas/")  # via django-storages -> Supabase Storage
    orden = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"Foto {self.orden} de {self.cancha.nombre}"


class HorarioDisponible(models.Model):
    cancha = models.ForeignKey(Cancha, on_delete=models.CASCADE)
    dia_semana = models.PositiveSmallIntegerField(null=True, blank=True)
    fecha_especifica = models.DateField(null=True, blank=True)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    tarifa = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cancha.nombre} {self.hora_inicio}-{self.hora_fin}"
