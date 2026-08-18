"""Puebla la base de datos con canchas de demostración para Pasto, Nariño.

Nota: `docs/prompt-diseno-nextjs-canchazo.md`, que según la documentación del
proyecto trae la tabla real de las 8 canchas de Pasto, no existe todavía en
este repositorio (ver `AVANCE.md`, Sprint 3). Los datos de este comando son
ficticios pero plausibles (barrios reales de Pasto, precios y coordenadas
aproximadas) solo para poder construir y probar el frontend de punta a punta.
Cuando el archivo real aparezca, reemplazar esta lista por los datos reales.
"""
from datetime import time

from django.core.management.base import BaseCommand
from django.db import transaction

from canchas.models import Cancha, Deporte, FotoCancha, HorarioDisponible
from usuarios.models import Usuario

CANCHAS_DEMO = [
    {
        "nombre": "Cancha Sintética El Ejido",
        "descripcion": "Cancha de fútbol 5 con grama sintética de última generación, junto al parque El Ejido.",
        "direccion": "Cra 27 #18-45, El Ejido",
        "barrio": "El Ejido",
        "latitud": 1.2143,
        "longitud": -77.2789,
        "telefono": "3201234501",
        "precio_base": 60000,
        "servicios": ["parqueadero", "iluminación", "baño", "cubierta"],
    },
    {
        "nombre": "Complejo Deportivo Tamasagra",
        "descripcion": "Dos canchas de fútbol 8 con gradería y zona de parqueo amplia.",
        "direccion": "Cl 20 #33-10, Tamasagra",
        "barrio": "Tamasagra",
        "latitud": 1.2261,
        "longitud": -77.2704,
        "telefono": "3201234502",
        "precio_base": 80000,
        "servicios": ["parqueadero", "iluminación", "graderías"],
    },
    {
        "nombre": "Cancha La Carolina",
        "descripcion": "Cancha techada de fútbol 5, ideal para jugar sin importar el clima de Pasto.",
        "direccion": "Cra 19 #14-22, La Carolina",
        "barrio": "La Carolina",
        "latitud": 1.2097,
        "longitud": -77.2822,
        "telefono": "3201234503",
        "precio_base": 55000,
        "servicios": ["cubierta", "baño", "iluminación"],
    },
    {
        "nombre": "Polideportivo Aranda",
        "descripcion": "Cancha múltiple de barrio con buena iluminación nocturna y ambiente familiar.",
        "direccion": "Cl 12 #8-30, Aranda",
        "barrio": "Aranda",
        "latitud": 1.1998,
        "longitud": -77.2734,
        "telefono": "3201234504",
        "precio_base": 45000,
        "servicios": ["iluminación", "baño"],
    },
    {
        "nombre": "Cancha Sintética Chapal",
        "descripcion": "Cancha nueva de fútbol 5 con marcador electrónico y zona de parqueo vigilada.",
        "direccion": "Cra 6 #10-15, Chapal",
        "barrio": "Chapal",
        "latitud": 1.2312,
        "longitud": -77.2665,
        "telefono": "3201234505",
        "precio_base": 70000,
        "servicios": ["parqueadero", "iluminación", "cubierta", "baño"],
    },
    {
        "nombre": "Cancha Torobajo",
        "descripcion": "Cancha de fútbol 5 cerca a la universidad, muy popular entre estudiantes.",
        "direccion": "Cl 18 #24-05, Torobajo",
        "barrio": "Torobajo",
        "latitud": 1.2178,
        "longitud": -77.2955,
        "telefono": "3201234506",
        "precio_base": 50000,
        "servicios": ["baño", "iluminación"],
    },
    {
        "nombre": "Cancha Panamericana Sur",
        "descripcion": "Amplia cancha de fútbol 8 sobre la vía Panamericana, ideal para partidos grandes.",
        "direccion": "Av. Panamericana Sur #45-60",
        "barrio": "Panamericana Sur",
        "latitud": 1.1889,
        "longitud": -77.2801,
        "telefono": "3201234507",
        "precio_base": 90000,
        "servicios": ["parqueadero", "graderías", "iluminación"],
    },
    {
        "nombre": "Cancha Champagnat",
        "descripcion": "Cancha sintética techada, cerca al centro de Pasto, con vestieres y duchas.",
        "direccion": "Cra 33 #16-20, Champagnat",
        "barrio": "Champagnat",
        "latitud": 1.2205,
        "longitud": -77.2748,
        "telefono": "3201234508",
        "precio_base": 65000,
        "servicios": ["cubierta", "baño", "parqueadero", "iluminación"],
    },
]

# Horarios ofrecidos cada día: tardes/noches entre semana, más mañanas el fin de semana.
HORAS_ENTRE_SEMANA = [(14, 15), (15, 16), (16, 17), (17, 18), (18, 19), (19, 20), (20, 21), (21, 22)]
HORAS_FIN_DE_SEMANA = [(8, 9), (9, 10), (10, 11), (11, 12), (14, 15), (15, 16), (16, 17), (17, 18), (18, 19), (19, 20)]


class Command(BaseCommand):
    help = "Crea (o reemplaza) datos de demostración: canchas de Pasto, horarios y sus admins."

    def handle(self, *args, **options):
        with transaction.atomic():
            deporte, _ = Deporte.objects.get_or_create(nombre="Fútbol")

            for i, datos in enumerate(CANCHAS_DEMO, start=1):
                username = f"admin.cancha{i}"
                admin, creado = Usuario.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": f"{username}@canchazo.test",
                        "celular": f"320111000{i}",
                        "rol": Usuario.ROL_ADMIN_CANCHA,
                        "consentimiento_datos_aceptado": True,
                    },
                )
                if creado:
                    admin.set_password("canchazo123")
                    admin.save()

                cancha, _ = Cancha.objects.update_or_create(
                    nombre=datos["nombre"],
                    defaults={
                        "descripcion": datos["descripcion"],
                        "direccion": datos["direccion"],
                        "latitud": datos["latitud"],
                        "longitud": datos["longitud"],
                        "telefono": datos["telefono"],
                        "deporte": deporte,
                        "servicios": datos["servicios"],
                        "estado": Cancha.ESTADO_APTO,
                        "administrador": admin,
                    },
                )

                HorarioDisponible.objects.filter(cancha=cancha).delete()
                horarios = []
                for dia_semana in range(7):
                    bloques = HORAS_FIN_DE_SEMANA if dia_semana >= 5 else HORAS_ENTRE_SEMANA
                    for hora_i, hora_f in bloques:
                        # Tarifa un poco más alta en horario pico (noche entre semana, fin de semana).
                        recargo = 1.15 if (dia_semana < 5 and hora_i >= 18) or dia_semana >= 5 else 1.0
                        horarios.append(
                            HorarioDisponible(
                                cancha=cancha,
                                dia_semana=dia_semana,
                                hora_inicio=time(hora_i, 0),
                                hora_fin=time(hora_f, 0),
                                tarifa=round(datos["precio_base"] * recargo, -3),
                            )
                        )
                HorarioDisponible.objects.bulk_create(horarios)

                self.stdout.write(f"  {datos['nombre']}: {len(horarios)} horarios ({'creada' if creado else 'actualizada'})")

        total_fotos = FotoCancha.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"Listo: {len(CANCHAS_DEMO)} canchas, deporte '{deporte.nombre}'. "
            f"Sin fotos cargadas todavía ({total_fotos} en total) — no hay archivos de imagen reales en el repo."
        ))
