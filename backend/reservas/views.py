from django.conf import settings
from django.utils.module_loading import import_string
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Reserva
from .serializers import (
    CalificacionSerializer,
    CalificarReservaSerializer,
    CrearReservaSerializer,
    MarcarAsistenciaSerializer,
    ReservaSerializer,
)
from .services import (
    CalificacionDuplicadaError,
    CanchaNoEncontradaError,
    HorarioNoDisponibleError,
    PermisoDenegadoError,
    TransicionInvalidaError,
    calificar_reserva,
    confirmar_pago_desde_webhook,
    crear_reserva,
    marcar_asistencia,
    reporte_cancha,
    reservas_visibles_para,
)


def _adaptador_pagos():
    return import_string(settings.ADAPTADOR_PAGOS)()


class ReservaViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ReservaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return reservas_visibles_para(self.request.user).select_related("cancha", "usuario")

    def create(self, request):
        entrada = CrearReservaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        try:
            reserva, cobro = crear_reserva(
                usuario=request.user,
                adaptador_pagos=_adaptador_pagos(),
                **entrada.validated_data,
            )
        except CanchaNoEncontradaError:
            return Response({"detail": "Cancha no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except HorarioNoDisponibleError:
            return Response(
                {"detail": "Ese horario ya no está disponible. Elegí otro."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {"reserva": ReservaSerializer(reserva).data, "url_pago": cobro["url_pago"]},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="marcar-asistencia")
    def marcar_asistencia(self, request, pk=None):
        entrada = MarcarAsistenciaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            reserva = marcar_asistencia(
                usuario=request.user, reserva_id=pk, **entrada.validated_data
            )
        except Reserva.DoesNotExist:
            return Response({"detail": "Reserva no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except PermisoDenegadoError:
            return Response({"detail": "No administras esta cancha."}, status=status.HTTP_403_FORBIDDEN)
        except TransicionInvalidaError:
            return Response(
                {"detail": "Solo se puede marcar asistencia sobre una reserva confirmada."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(ReservaSerializer(reserva).data)

    @action(detail=True, methods=["post"])
    def calificar(self, request, pk=None):
        entrada = CalificarReservaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            calificacion = calificar_reserva(
                usuario=request.user, reserva_id=pk, **entrada.validated_data
            )
        except Reserva.DoesNotExist:
            return Response({"detail": "Reserva no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except PermisoDenegadoError:
            return Response(
                {"detail": "No hiciste esta reserva ni administras esta cancha."},
                status=status.HTTP_403_FORBIDDEN,
            )
        except TransicionInvalidaError:
            return Response(
                {"detail": "Solo se puede calificar una reserva completada."},
                status=status.HTTP_409_CONFLICT,
            )
        except CalificacionDuplicadaError:
            return Response({"detail": "Ya calificaste esta reserva."}, status=status.HTTP_409_CONFLICT)

        return Response(CalificacionSerializer(calificacion).data, status=status.HTTP_201_CREATED)


class ReporteCanchaView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, cancha_id):
        try:
            reporte = reporte_cancha(usuario=request.user, cancha_id=cancha_id)
        except CanchaNoEncontradaError:
            return Response({"detail": "Cancha no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except PermisoDenegadoError:
            return Response({"detail": "No administras esta cancha."}, status=status.HTTP_403_FORBIDDEN)
        return Response(reporte)


class WompiWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        adaptador = _adaptador_pagos()
        if not adaptador.validar_firma_webhook(request.data):
            return Response({"detail": "Firma inválida."}, status=status.HTTP_400_BAD_REQUEST)

        confirmar_pago_desde_webhook(request.data, adaptador)
        return Response({"recibido": True})
