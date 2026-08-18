from django.contrib import admin

from .models import Calificacion, Pago, Reserva


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ("cancha", "usuario", "fecha", "hora_inicio", "hora_fin", "estado", "asistencia", "monto_anticipo")
    list_filter = ("estado", "asistencia", "cancha")


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ("reserva", "monto_total", "estado", "referencia_wompi", "fecha")
    list_filter = ("estado",)


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ("reserva", "calificado_por", "puntuacion", "fecha")
    list_filter = ("calificado_por",)
