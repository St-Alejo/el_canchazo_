from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    ROL_JUGADOR = "jugador"
    ROL_ADMIN_CANCHA = "admin_cancha"
    ROL_SUPERADMIN = "superadmin"
    ROL_CHOICES = [
        (ROL_JUGADOR, "Jugador"),
        (ROL_ADMIN_CANCHA, "Admin cancha"),
        (ROL_SUPERADMIN, "Superadmin"),
    ]

    celular = models.CharField(max_length=20, unique=True)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES)
    consentimiento_datos_aceptado = models.BooleanField(default=False)
    fecha_consentimiento = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username
