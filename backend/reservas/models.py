from django.conf import settings
from django.db import models

from canchas.models import Cancha


class Reserva(models.Model):
    ESTADO_PENDIENTE_PAGO = "pendiente_pago"
    ESTADO_CONFIRMADA = "confirmada"
    ESTADO_CANCELADA = "cancelada"
    ESTADO_COMPLETADA = "completada"
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE_PAGO, "Pendiente de pago"),
        (ESTADO_CONFIRMADA, "Confirmada"),
        (ESTADO_CANCELADA, "Cancelada"),
        (ESTADO_COMPLETADA, "Completada"),
    ]

    ASISTENCIA_SI_LLEGO = "asistio"
    ASISTENCIA_NO_LLEGO = "no_asistio"
    ASISTENCIA_CHOICES = [
        (ASISTENCIA_SI_LLEGO, "Sí llegó"),
        (ASISTENCIA_NO_LLEGO, "No llegó"),
    ]

    cancha = models.ForeignKey(Cancha, on_delete=models.PROTECT)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE_PAGO)
    monto_anticipo = models.DecimalField(max_digits=10, decimal_places=2)
    monto_tarifa_servicio = models.DecimalField(max_digits=10, decimal_places=2, default=500)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion_bloqueo = models.DateTimeField(null=True, blank=True)
    # No es un estado nuevo de `estado` (esos siguen siendo solo los 4 definidos arriba):
    # es un dato aparte que el admin de cancha registra tras el horario reservado, y que
    # dispara el paso a `completada` (ver `reservas/services.py::marcar_asistencia`).
    asistencia = models.CharField(max_length=20, choices=ASISTENCIA_CHOICES, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cancha", "fecha", "hora_inicio"],
                condition=models.Q(estado__in=["pendiente_pago", "confirmada"]),
                name="horario_unico_por_cancha",
            )
        ]

    def __str__(self):
        return f"{self.cancha.nombre} {self.fecha} {self.hora_inicio} ({self.estado})"


class Pago(models.Model):
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=30)
    referencia_wompi = models.CharField(max_length=100)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago {self.referencia_wompi} ({self.estado})"


class Calificacion(models.Model):
    CALIFICADO_POR_JUGADOR = "jugador"
    CALIFICADO_POR_CANCHA = "cancha"
    CALIFICADO_POR_CHOICES = [
        (CALIFICADO_POR_JUGADOR, "Jugador"),
        (CALIFICADO_POR_CANCHA, "Cancha"),
    ]

    reserva = models.ForeignKey(Reserva, related_name="calificaciones", on_delete=models.CASCADE)
    calificado_por = models.CharField(max_length=20, choices=CALIFICADO_POR_CHOICES)
    puntuacion = models.PositiveSmallIntegerField()
    comentario = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["reserva", "calificado_por"],
                name="una_calificacion_por_lado_y_reserva",
            )
        ]

    def __str__(self):
        return f"Calificacion {self.puntuacion} ({self.calificado_por})"
