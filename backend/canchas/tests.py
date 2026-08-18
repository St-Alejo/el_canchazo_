from datetime import date, time

from rest_framework import status
from rest_framework.test import APITestCase

from reservas.models import Reserva
from usuarios.models import Usuario

from .models import Cancha, Deporte, HorarioDisponible

URL_LISTA = "/api/canchas/"


class BusquedaCanchasTests(APITestCase):
    def setUp(self):
        self.futbol = Deporte.objects.create(nombre="Futbol")
        self.tenis = Deporte.objects.create(nombre="Tenis")

        admin = Usuario.objects.create_user(
            username="adminfutbol", celular="3001111111", password="clave-segura-123",
            rol=Usuario.ROL_ADMIN_CANCHA, consentimiento_datos_aceptado=True,
        )

        self.cancha_barata = Cancha.objects.create(
            nombre="La Cancha Barata", descripcion="", direccion="Barrio Centro",
            latitud=1.2, longitud=-77.2, telefono="3000000001", deporte=self.futbol,
            servicios=["parqueadero", "cubierta"], estado=Cancha.ESTADO_APTO, administrador=admin,
        )
        HorarioDisponible.objects.create(
            cancha=self.cancha_barata, dia_semana=0, hora_inicio=time(18, 0), hora_fin=time(19, 0), tarifa=30000,
        )

        self.cancha_cara = Cancha.objects.create(
            nombre="La Cancha Cara", descripcion="", direccion="Barrio Sur",
            latitud=1.3, longitud=-77.3, telefono="3000000002", deporte=self.futbol,
            servicios=["parqueadero"], estado=Cancha.ESTADO_APTO, administrador=admin,
        )
        HorarioDisponible.objects.create(
            cancha=self.cancha_cara, dia_semana=0, hora_inicio=time(18, 0), hora_fin=time(19, 0), tarifa=80000,
        )

        self.cancha_tenis = Cancha.objects.create(
            nombre="Cancha de Tenis", descripcion="", direccion="Barrio Norte",
            latitud=1.4, longitud=-77.4, telefono="3000000003", deporte=self.tenis,
            servicios=[], estado=Cancha.ESTADO_APTO, administrador=admin,
        )

        self.cancha_pendiente = Cancha.objects.create(
            nombre="Cancha Sin Aprobar", descripcion="", direccion="Barrio Centro",
            latitud=1.5, longitud=-77.5, telefono="3000000004", deporte=self.futbol,
            servicios=["parqueadero"], estado=Cancha.ESTADO_PENDIENTE, administrador=admin,
        )

    def test_lista_solo_incluye_canchas_aprobadas(self):
        respuesta = self.client.get(URL_LISTA)

        nombres = {c["nombre"] for c in respuesta.data}
        self.assertEqual(
            nombres, {"La Cancha Barata", "La Cancha Cara", "Cancha de Tenis"}
        )

    def test_filtro_por_deporte(self):
        respuesta = self.client.get(URL_LISTA, {"deporte": self.tenis.id})

        nombres = {c["nombre"] for c in respuesta.data}
        self.assertEqual(nombres, {"Cancha de Tenis"})

    def test_filtro_por_precio_maximo(self):
        respuesta = self.client.get(URL_LISTA, {"precio_max": "50000"})

        nombres = {c["nombre"] for c in respuesta.data}
        self.assertEqual(nombres, {"La Cancha Barata"})

    def test_filtro_por_precio_minimo(self):
        respuesta = self.client.get(URL_LISTA, {"precio_min": "50000"})

        nombres = {c["nombre"] for c in respuesta.data}
        self.assertEqual(nombres, {"La Cancha Cara"})

    def test_filtro_por_servicios(self):
        respuesta = self.client.get(URL_LISTA, {"servicios": "parqueadero,cubierta"})

        nombres = {c["nombre"] for c in respuesta.data}
        self.assertEqual(nombres, {"La Cancha Barata"})

    def test_filtro_por_ubicacion(self):
        respuesta = self.client.get(URL_LISTA, {"ubicacion": "Sur"})

        nombres = {c["nombre"] for c in respuesta.data}
        self.assertEqual(nombres, {"La Cancha Cara"})

    def test_detalle_de_cancha_no_aprobada_da_404(self):
        respuesta = self.client.get(f"{URL_LISTA}{self.cancha_pendiente.id}/")

        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_detalle_de_cancha_aprobada_incluye_precio_desde(self):
        respuesta = self.client.get(f"{URL_LISTA}{self.cancha_barata.id}/")

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["precio_desde"], "30000.00")


class DisponibilidadTests(APITestCase):
    def setUp(self):
        deporte = Deporte.objects.create(nombre="Futbol")
        admin = Usuario.objects.create_user(
            username="admin2", celular="3002222222", password="clave-segura-123",
            rol=Usuario.ROL_ADMIN_CANCHA, consentimiento_datos_aceptado=True,
        )
        jugador = Usuario.objects.create_user(
            username="jugador1", celular="3002222223", password="clave-segura-123",
            rol=Usuario.ROL_JUGADOR, consentimiento_datos_aceptado=True,
        )

        self.cancha = Cancha.objects.create(
            nombre="Cancha Disponibilidad", descripcion="", direccion="Barrio Centro",
            latitud=1.2, longitud=-77.2, telefono="3000000005", deporte=deporte,
            estado=Cancha.ESTADO_APTO, administrador=admin,
        )

        self.fecha = date(2026, 9, 7)  # lunes
        self.assertEqual(self.fecha.weekday(), 0)

        self.horario_libre = HorarioDisponible.objects.create(
            cancha=self.cancha, dia_semana=0, hora_inicio=time(18, 0), hora_fin=time(19, 0), tarifa=30000,
        )
        self.horario_ocupado = HorarioDisponible.objects.create(
            cancha=self.cancha, dia_semana=0, hora_inicio=time(19, 0), hora_fin=time(20, 0), tarifa=30000,
        )
        self.horario_otro_dia = HorarioDisponible.objects.create(
            cancha=self.cancha, dia_semana=1, hora_inicio=time(18, 0), hora_fin=time(19, 0), tarifa=30000,
        )
        self.horario_fecha_especifica = HorarioDisponible.objects.create(
            cancha=self.cancha, fecha_especifica=self.fecha, hora_inicio=time(21, 0), hora_fin=time(22, 0), tarifa=40000,
        )

        Reserva.objects.create(
            cancha=self.cancha, usuario=jugador, fecha=self.fecha,
            hora_inicio=self.horario_ocupado.hora_inicio, hora_fin=self.horario_ocupado.hora_fin,
            estado=Reserva.ESTADO_CONFIRMADA, monto_anticipo=15000,
        )

    def test_disponibilidad_excluye_horarios_ya_reservados_y_otros_dias(self):
        respuesta = self.client.get(f"{URL_LISTA}{self.cancha.id}/disponibilidad/", {"fecha": self.fecha.isoformat()})

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        ids = {h["id"] for h in respuesta.data}
        self.assertEqual(ids, {self.horario_libre.id, self.horario_fecha_especifica.id})

    def test_disponibilidad_requiere_fecha(self):
        respuesta = self.client.get(f"{URL_LISTA}{self.cancha.id}/disponibilidad/")

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
