from django.db.models import Min, Q

from reservas.models import Reserva

from .models import Cancha, HorarioDisponible


def listar_canchas(filtros):
    """Búsqueda pública de canchas: solo las aprobadas (`estado=apto`), con filtros opcionales."""
    queryset = (
        Cancha.objects.filter(estado=Cancha.ESTADO_APTO)
        .select_related("deporte")
        .annotate(precio_desde=Min("horariodisponible__tarifa"))
    )

    if filtros.get("deporte"):
        queryset = queryset.filter(deporte_id=filtros["deporte"])

    if filtros.get("ubicacion"):
        ubicacion = filtros["ubicacion"]
        queryset = queryset.filter(Q(nombre__icontains=ubicacion) | Q(direccion__icontains=ubicacion))

    if filtros.get("precio_min") is not None:
        queryset = queryset.filter(precio_desde__gte=filtros["precio_min"])

    if filtros.get("precio_max") is not None:
        queryset = queryset.filter(precio_desde__lte=filtros["precio_max"])

    canchas = list(queryset.order_by("nombre"))

    # Filtrado por servicios en Python: `JSONField.__contains` no es portable entre
    # Postgres y sqlite, y el volumen de canchas del MVP (Pasto) es pequeño.
    servicios = filtros.get("servicios")
    if servicios:
        requeridos = set(servicios)
        canchas = [c for c in canchas if requeridos.issubset(set(c.servicios))]

    return canchas


def obtener_cancha_publicada(pk):
    return (
        Cancha.objects.filter(estado=Cancha.ESTADO_APTO)
        .select_related("deporte")
        .annotate(precio_desde=Min("horariodisponible__tarifa"))
        .get(pk=pk)
    )


def horarios_disponibles(cancha, fecha):
    """Horarios de la cancha para `fecha`, excluyendo los que ya tienen una reserva activa.

    Un horario aplica a `fecha` si coincide con su `fecha_especifica`, o si es recurrente
    (`fecha_especifica` vacío) y su `dia_semana` coincide con `fecha.weekday()` (0=lunes).
    """
    horarios = (
        HorarioDisponible.objects.filter(cancha=cancha)
        .filter(Q(fecha_especifica=fecha) | Q(fecha_especifica__isnull=True, dia_semana=fecha.weekday()))
        .order_by("hora_inicio")
    )

    horas_ocupadas = set(
        Reserva.objects.filter(
            cancha=cancha,
            fecha=fecha,
            estado__in=[Reserva.ESTADO_PENDIENTE_PAGO, Reserva.ESTADO_CONFIRMADA],
        ).values_list("hora_inicio", flat=True)
    )

    return [h for h in horarios if h.hora_inicio not in horas_ocupadas]
