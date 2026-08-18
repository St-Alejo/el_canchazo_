from datetime import date, time, timedelta
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from canchas.models import Cancha, Deporte, HorarioDisponible
from usuarios.models import Usuario

from .adapters.fake import AdaptadorPagosFalso
from .models import Pago, Reserva
from .services import HorarioNoDisponibleError, crear_reserva

URL_LISTA = "/api/reservas/"
URL_WEBHOOK = "/api/webhooks/wompi/"
ADAPTADOR_FALSO = "reservas.adapters.fake.AdaptadorPagosFalso"


class AislamientoReservasTests(APITestCase):
    def setUp(self):
        self.deporte = Deporte.objects.create(nombre="Futbol")

        self.admin_1 = Usuario.objects.create_user(
            username="admin1", celular="3000000001", password="clave-segura-123",
            rol=Usuario.ROL_ADMIN_CANCHA, consentimiento_datos_aceptado=True,
        )
        self.admin_2 = Usuario.objects.create_user(
            username="admin2", celular="3000000002", password="clave-segura-123",
            rol=Usuario.ROL_ADMIN_CANCHA, consentimiento_datos_aceptado=True,
        )
        self.jugador_1 = Usuario.objects.create_user(
            username="jugador1", celular="3000000003", password="clave-segura-123",
            rol=Usuario.ROL_JUGADOR, consentimiento_datos_aceptado=True,
        )
        self.jugador_2 = Usuario.objects.create_user(
            username="jugador2", celular="3000000004", password="clave-segura-123",
            rol=Usuario.ROL_JUGADOR, consentimiento_datos_aceptado=True,
        )

        self.cancha_1 = Cancha.objects.create(
            nombre="Cancha Uno", descripcion="", direccion="Calle 1", latitud=1.2,
            longitud=-77.2, telefono="3000000001", deporte=self.deporte,
            administrador=self.admin_1,
        )
        self.cancha_2 = Cancha.objects.create(
            nombre="Cancha Dos", descripcion="", direccion="Calle 2", latitud=1.3,
            longitud=-77.3, telefono="3000000002", deporte=self.deporte,
            administrador=self.admin_2,
        )

        self.reserva_cancha_1 = Reserva.objects.create(
            cancha=self.cancha_1, usuario=self.jugador_1, fecha=date(2026, 9, 1),
            hora_inicio=time(18, 0), hora_fin=time(19, 0), monto_anticipo=20000,
        )
        self.reserva_cancha_2 = Reserva.objects.create(
            cancha=self.cancha_2, usuario=self.jugador_2, fecha=date(2026, 9, 1),
            hora_inicio=time(19, 0), hora_fin=time(20, 0), monto_anticipo=20000,
        )

    def test_admin_cancha_solo_ve_reservas_de_su_propia_cancha(self):
        self.client.force_authenticate(self.admin_1)

        respuesta = self.client.get(URL_LISTA)

        ids = {reserva["id"] for reserva in respuesta.data}
        self.assertEqual(ids, {self.reserva_cancha_1.id})

    def test_admin_cancha_no_puede_leer_reserva_de_otra_cancha_por_id(self):
        self.client.force_authenticate(self.admin_1)

        respuesta = self.client.get(f"{URL_LISTA}{self.reserva_cancha_2.id}/")

        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_jugador_solo_ve_sus_propias_reservas(self):
        self.client.force_authenticate(self.jugador_1)

        respuesta = self.client.get(URL_LISTA)

        ids = {reserva["id"] for reserva in respuesta.data}
        self.assertEqual(ids, {self.reserva_cancha_1.id})

    def test_jugador_no_puede_leer_reserva_de_otro_usuario_por_id(self):
        self.client.force_authenticate(self.jugador_1)

        respuesta = self.client.get(f"{URL_LISTA}{self.reserva_cancha_2.id}/")

        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonimo_no_puede_listar_reservas(self):
        respuesta = self.client.get(URL_LISTA)

        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(ADAPTADOR_PAGOS=ADAPTADOR_FALSO)
class CrearReservaTests(APITestCase):
    def setUp(self):
        deporte = Deporte.objects.create(nombre="Futbol")
        admin = Usuario.objects.create_user(
            username="admin3", celular="3003333333", password="clave-segura-123",
            rol=Usuario.ROL_ADMIN_CANCHA, consentimiento_datos_aceptado=True,
        )
        self.jugador = Usuario.objects.create_user(
            username="jugador3", celular="3003333334", password="clave-segura-123",
            rol=Usuario.ROL_JUGADOR, consentimiento_datos_aceptado=True,
        )
        self.cancha = Cancha.objects.create(
            nombre="Cancha Reservable", descripcion="", direccion="Barrio Centro",
            latitud=1.2, longitud=-77.2, telefono="3000000006", deporte=deporte,
            estado=Cancha.ESTADO_APTO, administrador=admin,
        )
        self.fecha = date(2026, 9, 7)  # lunes
        self.horario = HorarioDisponible.objects.create(
            cancha=self.cancha, dia_semana=self.fecha.weekday(),
            hora_inicio=time(18, 0), hora_fin=time(19, 0), tarifa=30000,
        )
        self.datos = {
            "cancha_id": self.cancha.id,
            "fecha": self.fecha.isoformat(),
            "hora_inicio": "18:00:00",
            "redirect_url": "https://elcanchazo.test/gracias",
        }

    def test_crear_reserva_exitosa_queda_pendiente_de_pago(self):
        self.client.force_authenticate(self.jugador)

        respuesta = self.client.post(URL_LISTA, self.datos, format="json")

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertIn("url_pago", respuesta.data)

        reserva = Reserva.objects.get(cancha=self.cancha, fecha=self.fecha, hora_inicio=time(18, 0))
        self.assertEqual(reserva.estado, Reserva.ESTADO_PENDIENTE_PAGO)
        self.assertEqual(reserva.monto_anticipo, 30000)
        self.assertIsNotNone(reserva.fecha_expiracion_bloqueo)

        pago = Pago.objects.get(reserva=reserva)
        self.assertEqual(pago.monto_total, 30500)  # anticipo + $500 de tarifa de servicio
        self.assertEqual(pago.estado, "PENDING")

    def test_no_se_puede_reservar_un_horario_que_no_existe(self):
        self.client.force_authenticate(self.jugador)
        datos = dict(self.datos, hora_inicio="23:00:00")

        respuesta = self.client.post(URL_LISTA, datos, format="json")

        self.assertEqual(respuesta.status_code, status.HTTP_409_CONFLICT)

    def test_no_se_puede_reservar_una_cancha_no_aprobada(self):
        self.cancha.estado = Cancha.ESTADO_PENDIENTE
        self.cancha.save(update_fields=["estado"])
        self.client.force_authenticate(self.jugador)

        respuesta = self.client.post(URL_LISTA, self.datos, format="json")

        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_el_monto_lo_calcula_el_servidor_no_el_cliente(self):
        self.client.force_authenticate(self.jugador)
        datos = dict(self.datos, monto_anticipo="1")  # el serializer ni siquiera tiene este campo

        respuesta = self.client.post(URL_LISTA, datos, format="json")

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        reserva = Reserva.objects.get(cancha=self.cancha, fecha=self.fecha, hora_inicio=time(18, 0))
        self.assertEqual(reserva.monto_anticipo, 30000)

    def test_segundo_intento_sobre_el_mismo_horario_recibe_409(self):
        self.client.force_authenticate(self.jugador)

        primera = self.client.post(URL_LISTA, self.datos, format="json")
        self.assertEqual(primera.status_code, status.HTTP_201_CREATED)

        segunda = self.client.post(URL_LISTA, self.datos, format="json")
        self.assertEqual(segunda.status_code, status.HTTP_409_CONFLICT)

        self.assertEqual(
            Reserva.objects.filter(cancha=self.cancha, fecha=self.fecha, hora_inicio=time(18, 0)).count(), 1
        )

    def test_el_unique_constraint_de_bd_protege_incluso_si_el_prechequeo_queda_desactualizado(self):
        """Simula la carrera real: el pre-chequeo de disponibilidad todavía "ve" el horario
        libre (como pasaría si dos requests llegan casi al mismo tiempo), pero la fila
        conflictiva ya existe cuando el INSERT se ejecuta. El UniqueConstraint de la base
        de datos es quien de verdad rechaza el segundo intento, no el pre-chequeo."""
        Reserva.objects.create(
            cancha=self.cancha, usuario=self.jugador, fecha=self.fecha,
            hora_inicio=self.horario.hora_inicio, hora_fin=self.horario.hora_fin,
            estado=Reserva.ESTADO_PENDIENTE_PAGO, monto_anticipo=self.horario.tarifa,
        )

        with patch("reservas.services.horarios_disponibles_de_cancha", return_value=[self.horario]):
            with self.assertRaises(HorarioNoDisponibleError):
                crear_reserva(
                    usuario=self.jugador, cancha_id=self.cancha.id, fecha=self.fecha,
                    hora_inicio=self.horario.hora_inicio, redirect_url="https://elcanchazo.test/gracias",
                    adaptador_pagos=AdaptadorPagosFalso(),
                )


@override_settings(ADAPTADOR_PAGOS=ADAPTADOR_FALSO)
class WebhookWompiTests(APITestCase):
    def setUp(self):
        deporte = Deporte.objects.create(nombre="Futbol")
        admin = Usuario.objects.create_user(
            username="admin4", celular="3004444444", password="clave-segura-123",
            rol=Usuario.ROL_ADMIN_CANCHA, consentimiento_datos_aceptado=True,
        )
        self.jugador = Usuario.objects.create_user(
            username="jugador4", celular="3004444445", password="clave-segura-123",
            rol=Usuario.ROL_JUGADOR, consentimiento_datos_aceptado=True,
        )
        self.cancha = Cancha.objects.create(
            nombre="Cancha Webhook", descripcion="", direccion="Barrio Centro",
            latitud=1.2, longitud=-77.2, telefono="3000000007", deporte=deporte,
            estado=Cancha.ESTADO_APTO, administrador=admin,
        )
        fecha = date(2026, 9, 7)  # lunes
        HorarioDisponible.objects.create(
            cancha=self.cancha, dia_semana=fecha.weekday(),
            hora_inicio=time(18, 0), hora_fin=time(19, 0), tarifa=30000,
        )

        self.client.force_authenticate(self.jugador)
        creacion = self.client.post(
            URL_LISTA,
            {
                "cancha_id": self.cancha.id, "fecha": fecha.isoformat(),
                "hora_inicio": "18:00:00", "redirect_url": "https://elcanchazo.test/gracias",
            },
            format="json",
        )
        self.reserva_id = creacion.data["reserva"]["id"]
        self.referencia = Pago.objects.get(reserva_id=self.reserva_id).referencia_wompi
        self.client.force_authenticate(None)  # el webhook lo llama Wompi, no un usuario logueado

    def test_pago_aprobado_confirma_la_reserva(self):
        payload = {
            "signature": {"checksum": AdaptadorPagosFalso.CHECKSUM_VALIDO},
            "referencia": self.referencia,
            "estado": "APPROVED",
        }

        respuesta = self.client.post(URL_WEBHOOK, payload, format="json")

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        reserva = Reserva.objects.get(pk=self.reserva_id)
        self.assertEqual(reserva.estado, Reserva.ESTADO_CONFIRMADA)
        self.assertIsNone(reserva.fecha_expiracion_bloqueo)
        self.assertEqual(Pago.objects.get(reserva_id=self.reserva_id).estado, "APPROVED")

    def test_webhook_con_firma_invalida_no_confirma_nada(self):
        payload = {
            "signature": {"checksum": "firma-inventada"},
            "referencia": self.referencia,
            "estado": "APPROVED",
        }

        respuesta = self.client.post(URL_WEBHOOK, payload, format="json")

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        reserva = Reserva.objects.get(pk=self.reserva_id)
        self.assertEqual(reserva.estado, Reserva.ESTADO_PENDIENTE_PAGO)

    def test_webhook_duplicado_es_idempotente(self):
        payload = {
            "signature": {"checksum": AdaptadorPagosFalso.CHECKSUM_VALIDO},
            "referencia": self.referencia,
            "estado": "APPROVED",
        }

        self.client.post(URL_WEBHOOK, payload, format="json")
        segunda = self.client.post(URL_WEBHOOK, payload, format="json")

        self.assertEqual(segunda.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Reserva.objects.filter(pk=self.reserva_id, estado=Reserva.ESTADO_CONFIRMADA).count(), 1
        )

    def test_pago_rechazado_no_confirma_la_reserva(self):
        payload = {
            "signature": {"checksum": AdaptadorPagosFalso.CHECKSUM_VALIDO},
            "referencia": self.referencia,
            "estado": "DECLINED",
        }

        respuesta = self.client.post(URL_WEBHOOK, payload, format="json")

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        reserva = Reserva.objects.get(pk=self.reserva_id)
        self.assertEqual(reserva.estado, Reserva.ESTADO_PENDIENTE_PAGO)
        self.assertEqual(Pago.objects.get(reserva_id=self.reserva_id).estado, "DECLINED")


class ComandoLiberarReservasVencidasTests(TestCase):
    def setUp(self):
        deporte = Deporte.objects.create(nombre="Futbol")
        admin = Usuario.objects.create_user(
            username="admin5", celular="3005555555", password="clave-segura-123",
            rol=Usuario.ROL_ADMIN_CANCHA, consentimiento_datos_aceptado=True,
        )
        jugador = Usuario.objects.create_user(
            username="jugador5", celular="3005555556", password="clave-segura-123",
            rol=Usuario.ROL_JUGADOR, consentimiento_datos_aceptado=True,
        )
        cancha = Cancha.objects.create(
            nombre="Cancha Vencida", descripcion="", direccion="Barrio Centro",
            latitud=1.2, longitud=-77.2, telefono="3000000008", deporte=deporte,
            estado=Cancha.ESTADO_APTO, administrador=admin,
        )
        fecha = date(2026, 9, 7)

        self.vencida = Reserva.objects.create(
            cancha=cancha, usuario=jugador, fecha=fecha, hora_inicio=time(18, 0), hora_fin=time(19, 0),
            estado=Reserva.ESTADO_PENDIENTE_PAGO, monto_anticipo=30000,
            fecha_expiracion_bloqueo=timezone.now() - timedelta(minutes=1),
        )
        self.vigente = Reserva.objects.create(
            cancha=cancha, usuario=jugador, fecha=fecha, hora_inicio=time(20, 0), hora_fin=time(21, 0),
            estado=Reserva.ESTADO_PENDIENTE_PAGO, monto_anticipo=30000,
            fecha_expiracion_bloqueo=timezone.now() + timedelta(minutes=10),
        )
        self.confirmada = Reserva.objects.create(
            cancha=cancha, usuario=jugador, fecha=fecha, hora_inicio=time(22, 0), hora_fin=time(23, 0),
            estado=Reserva.ESTADO_CONFIRMADA, monto_anticipo=30000, fecha_expiracion_bloqueo=None,
        )

    def test_comando_libera_solo_las_vencidas(self):
        call_command("liberar_reservas_vencidas")

        self.vencida.refresh_from_db()
        self.vigente.refresh_from_db()
        self.confirmada.refresh_from_db()

        self.assertEqual(self.vencida.estado, Reserva.ESTADO_CANCELADA)
        self.assertEqual(self.vigente.estado, Reserva.ESTADO_PENDIENTE_PAGO)
        self.assertEqual(self.confirmada.estado, Reserva.ESTADO_CONFIRMADA)


class CicloAsistenciaYCalificacionTests(APITestCase):
    """Sprint 7: marcar asistencia, calificación bidireccional, con dos usuarios de prueba."""

    def setUp(self):
        deporte = Deporte.objects.create(nombre="Futbol")
        self.admin = Usuario.objects.create_user(
            username="admin6", celular="3006666666", password="clave-segura-123",
            rol=Usuario.ROL_ADMIN_CANCHA, consentimiento_datos_aceptado=True,
        )
        self.otro_admin = Usuario.objects.create_user(
            username="admin7", celular="3006666667", password="clave-segura-123",
            rol=Usuario.ROL_ADMIN_CANCHA, consentimiento_datos_aceptado=True,
        )
        self.jugador = Usuario.objects.create_user(
            username="jugador6", celular="3006666668", password="clave-segura-123",
            rol=Usuario.ROL_JUGADOR, consentimiento_datos_aceptado=True,
        )
        self.otro_jugador = Usuario.objects.create_user(
            username="jugador7", celular="3006666669", password="clave-segura-123",
            rol=Usuario.ROL_JUGADOR, consentimiento_datos_aceptado=True,
        )
        self.cancha = Cancha.objects.create(
            nombre="Cancha Confianza", descripcion="", direccion="Barrio Centro",
            latitud=1.2, longitud=-77.2, telefono="3000000009", deporte=deporte,
            estado=Cancha.ESTADO_APTO, administrador=self.admin,
        )
        self.reserva = Reserva.objects.create(
            cancha=self.cancha, usuario=self.jugador, fecha=date(2026, 9, 7),
            hora_inicio=time(18, 0), hora_fin=time(19, 0),
            estado=Reserva.ESTADO_CONFIRMADA, monto_anticipo=30000,
        )
        self.url_asistencia = f"{URL_LISTA}{self.reserva.id}/marcar-asistencia/"
        self.url_calificar = f"{URL_LISTA}{self.reserva.id}/calificar/"

    def test_admin_de_otra_cancha_no_puede_marcar_asistencia(self):
        self.client.force_authenticate(self.otro_admin)

        respuesta = self.client.post(self.url_asistencia, {"asistencia": "asistio"}, format="json")

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_se_puede_calificar_antes_de_marcar_asistencia(self):
        self.client.force_authenticate(self.jugador)

        respuesta = self.client.post(self.url_calificar, {"puntuacion": 5}, format="json")

        self.assertEqual(respuesta.status_code, status.HTTP_409_CONFLICT)

    def test_ciclo_completo_marcar_asistencia_y_calificacion_bidireccional(self):
        self.client.force_authenticate(self.admin)
        respuesta = self.client.post(self.url_asistencia, {"asistencia": "asistio"}, format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["estado"], Reserva.ESTADO_COMPLETADA)
        self.assertEqual(respuesta.data["asistencia"], "asistio")

        # El jugador califica la cancha.
        self.client.force_authenticate(self.jugador)
        resp_jugador = self.client.post(
            self.url_calificar, {"puntuacion": 5, "comentario": "Muy buena cancha"}, format="json"
        )
        self.assertEqual(resp_jugador.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp_jugador.data["calificado_por"], "jugador")

        # La cancha (su admin) califica al jugador.
        self.client.force_authenticate(self.admin)
        resp_cancha = self.client.post(self.url_calificar, {"puntuacion": 4}, format="json")
        self.assertEqual(resp_cancha.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp_cancha.data["calificado_por"], "cancha")

        self.assertEqual(self.reserva.calificaciones.count(), 2)

    def test_no_se_puede_calificar_dos_veces_del_mismo_lado(self):
        self.client.force_authenticate(self.admin)
        self.client.post(self.url_asistencia, {"asistencia": "no_asistio"}, format="json")

        self.client.force_authenticate(self.jugador)
        primera = self.client.post(self.url_calificar, {"puntuacion": 3}, format="json")
        segunda = self.client.post(self.url_calificar, {"puntuacion": 1}, format="json")

        self.assertEqual(primera.status_code, status.HTTP_201_CREATED)
        self.assertEqual(segunda.status_code, status.HTTP_409_CONFLICT)

    def test_usuario_ajeno_no_puede_calificar(self):
        self.client.force_authenticate(self.admin)
        self.client.post(self.url_asistencia, {"asistencia": "asistio"}, format="json")

        self.client.force_authenticate(self.otro_jugador)
        respuesta = self.client.post(self.url_calificar, {"puntuacion": 5}, format="json")

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)


class ReporteCanchaTests(APITestCase):
    def setUp(self):
        deporte = Deporte.objects.create(nombre="Futbol")
        self.admin = Usuario.objects.create_user(
            username="admin8", celular="3008888888", password="clave-segura-123",
            rol=Usuario.ROL_ADMIN_CANCHA, consentimiento_datos_aceptado=True,
        )
        self.otro_admin = Usuario.objects.create_user(
            username="admin9", celular="3008888889", password="clave-segura-123",
            rol=Usuario.ROL_ADMIN_CANCHA, consentimiento_datos_aceptado=True,
        )
        jugador = Usuario.objects.create_user(
            username="jugador8", celular="3008888890", password="clave-segura-123",
            rol=Usuario.ROL_JUGADOR, consentimiento_datos_aceptado=True,
        )
        self.cancha = Cancha.objects.create(
            nombre="Cancha Reporte", descripcion="", direccion="Barrio Centro",
            latitud=1.2, longitud=-77.2, telefono="3000000010", deporte=deporte,
            estado=Cancha.ESTADO_APTO, administrador=self.admin,
        )
        Reserva.objects.create(
            cancha=self.cancha, usuario=jugador, fecha=date(2026, 9, 7),
            hora_inicio=time(18, 0), hora_fin=time(19, 0),
            estado=Reserva.ESTADO_CONFIRMADA, monto_anticipo=30000,
        )
        Reserva.objects.create(
            cancha=self.cancha, usuario=jugador, fecha=date(2026, 9, 8),
            hora_inicio=time(18, 0), hora_fin=time(19, 0),
            estado=Reserva.ESTADO_CANCELADA, monto_anticipo=30000,
        )
        self.url = f"/api/reservas/reporte/{self.cancha.id}/"

    def test_admin_ve_el_reporte_de_su_cancha(self):
        self.client.force_authenticate(self.admin)

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["total_reservas"], 2)
        self.assertEqual(respuesta.data["ingresos_confirmados"], 30000)

    def test_admin_de_otra_cancha_no_puede_ver_el_reporte(self):
        self.client.force_authenticate(self.otro_admin)

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
