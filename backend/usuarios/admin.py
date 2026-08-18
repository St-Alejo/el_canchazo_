from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Canchazo", {"fields": ("celular", "rol", "consentimiento_datos_aceptado", "fecha_consentimiento")}),
    )
    list_display = ("username", "email", "celular", "rol", "is_staff")
