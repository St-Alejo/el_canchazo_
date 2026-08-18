from django.contrib import admin

from .models import Cancha, Deporte, FotoCancha, HorarioDisponible


class FotoCanchaInline(admin.TabularInline):
    model = FotoCancha
    extra = 1


class HorarioDisponibleInline(admin.TabularInline):
    model = HorarioDisponible
    extra = 1


@admin.register(Deporte)
class DeporteAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")


@admin.register(Cancha)
class CanchaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "deporte", "estado", "administrador", "fecha_registro")
    list_filter = ("estado", "deporte")
    inlines = [FotoCanchaInline, HorarioDisponibleInline]


@admin.register(HorarioDisponible)
class HorarioDisponibleAdmin(admin.ModelAdmin):
    list_display = ("cancha", "dia_semana", "fecha_especifica", "hora_inicio", "hora_fin", "tarifa")
    list_filter = ("cancha",)
