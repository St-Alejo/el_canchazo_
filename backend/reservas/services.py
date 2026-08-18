from datetime import timedelta

from django.db import IntegrityError, models, transaction
from django.utils import timezone

from canchas.models import Cancha
from canchas.services import horarios_disponibles as horarios_disponibles_de_cancha
from usuarios.models import Usuario

from .models import Calificacion, Pago, Reserva

MINUTOS_EXPIRACION_BLOQUEO = 10
ESTADOS_PAGO_APROBADOS = {"APPROVED"}


class CanchaNoEncontradaError(Exception):
    """No existe una cancha aprobada (`estado=apto`) con ese id."""


class HorarioNoDisponibleError(Exception):
    """El horario pedido no está definido para la cancha, o ya tiene una reserva activa."""


class PermisoDenegadoError(Exception):
    """El usuario no tiene relación con la reserva (ni es quien la hizo, ni administra la cancha)."""


class TransicionInvalidaError(Exception):
    """La reserva no está en un estado que permita la operación pedida."""


class CalificacionDuplicadaError(Exception):
    """Ese lado (jugador o cancha) ya calificó esta reserva."""


def reservas_visibles_para(usuario):
    """Un admin_cancha solo ve reservas de su propia cancha; un jugador, solo las suyas."""
    if usuario.is_superuser or usuario.rol == Usuario.ROL_SUPERADMIN:
        return Reserva.objects.all()
    if usuario.rol == Usuario.ROL_ADMIN_CANCHA:
        return Reserva.objects.filter(cancha__administrador=usuario)
    return Reserva.objects.filter(usuario=usuario)


def crear_reserva(*, usuario, cancha_id, fecha, hora_inicio, redirect_url, adaptador_pagos):
    """Crea la reserva en `pendiente_pago` e inicia el cobro del anticipo con Wompi.

    El monto del anticipo sale de `HorarioDisponible.tarifa` calculado en el servidor,
    nunca del cliente, para que nadie pueda manipular cuánto paga por una reserva.
    """
    try:
        cancha = Cancha.objects.get(pk=cancha_id, estado=Cancha.ESTADO_APTO)
    except Cancha.DoesNotExist as exc:
        raise CanchaNoEncontradaError from exc

    horario = next(
        (h for h in horarios_disponibles_de_cancha(cancha, fecha) if h.hora_inicio == hora_inicio),
        None,
    )
    if horario is None:
        raise HorarioNoDisponibleError

    try:
        with transaction.atomic():
            reserva = Reserva.objects.create(
                cancha=cancha,
                usuario=usuario,
                fecha=fecha,
                hora_inicio=horario.hora_inicio,
                hora_fin=horario.hora_fin,
                estado=Reserva.ESTADO_PENDIENTE_PAGO,
                monto_anticipo=horario.tarifa,
                fecha_expiracion_bloqueo=timezone.now() + timedelta(minutes=MINUTOS_EXPIRACION_BLOQUEO),
            )
    except IntegrityError as exc:
        # Misma condición que ya descartó el pre-chequeo de arriba: si dos requests
        # llegaron casi al mismo tiempo, el UniqueConstraint de la base de datos es
        # quien de verdad decide cuál de las dos gana la carrera.
        raise HorarioNoDisponibleError from exc

    monto_total = reserva.monto_anticipo + reserva.monto_tarifa_servicio
    cobro = adaptador_pagos.crear_cobro(
        referencia=f"reserva-{reserva.id}",
        monto_total_centavos=int(monto_total * 100),
        descripcion=f"Anticipo {cancha.nombre} - {fecha.isoformat()}",
        redirect_url=redirect_url,
    )
    Pago.objects.create(reserva=reserva, monto_total=monto_total, estado="PENDING", referencia_wompi=cobro["referencia"])
    return reserva, cobro


def liberar_reservas_vencidas(ahora=None):
    """Cancela las reservas `pendiente_pago` cuyo bloqueo temporal ya expiró sin pago."""
    ahora = ahora or timezone.now()
    return Reserva.objects.filter(
        estado=Reserva.ESTADO_PENDIENTE_PAGO,
        fecha_expiracion_bloqueo__lt=ahora,
    ).update(estado=Reserva.ESTADO_CANCELADA)


def confirmar_pago_desde_webhook(payload, adaptador_pagos):
    """Aplica un evento de pago ya autenticado (la vista valida la firma antes de llamar acá).

    Idempotente: si la reserva ya estaba `confirmada`, no vuelve a tocar nada — así un
    webhook duplicado de Wompi no rompe el estado ni reprocesa el pago.
    """
    confirmacion = adaptador_pagos.extraer_confirmacion(payload)
    if confirmacion is None:
        return None

    try:
        pago = Pago.objects.select_related("reserva").get(referencia_wompi=confirmacion["referencia"])
    except Pago.DoesNotExist:
        return None

    reserva = pago.reserva
    if reserva.estado == Reserva.ESTADO_CONFIRMADA:
        return reserva

    pago.estado = confirmacion["estado"]
    pago.save(update_fields=["estado"])

    if confirmacion["estado"] in ESTADOS_PAGO_APROBADOS and reserva.estado == Reserva.ESTADO_PENDIENTE_PAGO:
        reserva.estado = Reserva.ESTADO_CONFIRMADA
        reserva.fecha_expiracion_bloqueo = None
        reserva.save(update_fields=["estado", "fecha_expiracion_bloqueo"])

    return reserva


def marcar_asistencia(*, usuario, reserva_id, asistencia):
    """El admin de la cancha registra si el jugador llegó o no.

    Solo se puede marcar sobre una reserva `confirmada` de la propia cancha del admin.
    Marcar la asistencia (en cualquiera de los dos sentidos) cierra el ciclo de la
    reserva y la pasa a `completada`, que es lo que habilita calificar (sección 7 del
    roadmap: "cerrar el círculo de confianza").
    """
    try:
        reserva = Reserva.objects.select_related("cancha").get(pk=reserva_id)
    except Reserva.DoesNotExist as exc:
        raise Reserva.DoesNotExist from exc

    if reserva.cancha.administrador_id != usuario.id and not usuario.is_superuser:
        raise PermisoDenegadoError

    if reserva.estado != Reserva.ESTADO_CONFIRMADA:
        raise TransicionInvalidaError

    reserva.asistencia = asistencia
    reserva.estado = Reserva.ESTADO_COMPLETADA
    reserva.save(update_fields=["asistencia", "estado"])
    return reserva


def calificar_reserva(*, usuario, reserva_id, puntuacion, comentario):
    """Calificación bidireccional: el jugador califica la cancha, la cancha califica al jugador.

    Quién calificó lo decide la relación del usuario autenticado con la reserva, no un
    parámetro del cliente. Solo procede si la reserva ya está `completada` y ese lado
    todavía no había calificado (el `UniqueConstraint` del modelo es la garantía real).
    """
    try:
        reserva = Reserva.objects.select_related("cancha").get(pk=reserva_id)
    except Reserva.DoesNotExist as exc:
        raise Reserva.DoesNotExist from exc

    if usuario.id == reserva.usuario_id:
        calificado_por = Calificacion.CALIFICADO_POR_JUGADOR
    elif usuario.id == reserva.cancha.administrador_id:
        calificado_por = Calificacion.CALIFICADO_POR_CANCHA
    else:
        raise PermisoDenegadoError

    if reserva.estado != Reserva.ESTADO_COMPLETADA:
        raise TransicionInvalidaError

    try:
        return Calificacion.objects.create(
            reserva=reserva,
            calificado_por=calificado_por,
            puntuacion=puntuacion,
            comentario=comentario,
        )
    except IntegrityError as exc:
        raise CalificacionDuplicadaError from exc


def reporte_cancha(*, usuario, cancha_id):
    """Reporte básico de reservas y tráfico para el equipo de la cancha (Sprint 7)."""
    try:
        cancha = Cancha.objects.get(pk=cancha_id)
    except Cancha.DoesNotExist as exc:
        raise CanchaNoEncontradaError from exc

    if cancha.administrador_id != usuario.id and not usuario.is_superuser:
        raise PermisoDenegadoError

    reservas = Reserva.objects.filter(cancha=cancha)
    por_estado = {estado: 0 for estado, _ in Reserva.ESTADO_CHOICES}
    for fila in reservas.values("estado").annotate(total=models.Count("id")):
        por_estado[fila["estado"]] = fila["total"]

    ingresos = reservas.filter(
        estado__in=[Reserva.ESTADO_CONFIRMADA, Reserva.ESTADO_COMPLETADA]
    ).aggregate(total=models.Sum("monto_anticipo"))["total"] or 0

    asistieron = reservas.filter(asistencia=Reserva.ASISTENCIA_SI_LLEGO).count()
    no_asistieron = reservas.filter(asistencia=Reserva.ASISTENCIA_NO_LLEGO).count()

    return {
        "cancha_id": cancha.id,
        "cancha_nombre": cancha.nombre,
        "total_reservas": reservas.count(),
        "por_estado": por_estado,
        "ingresos_confirmados": ingresos,
        "asistieron": asistieron,
        "no_asistieron": no_asistieron,
    }
