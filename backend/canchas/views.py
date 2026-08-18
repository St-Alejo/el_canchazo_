from django.http import Http404
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cancha
from .serializers import (
    CanchaDetailSerializer,
    CanchaListSerializer,
    DisponibilidadQuerySerializer,
    FiltroCanchaSerializer,
    HorarioDisponibleSerializer,
)
from .services import horarios_disponibles, listar_canchas, obtener_cancha_publicada


class CanchaListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        filtros = FiltroCanchaSerializer(data=request.query_params)
        filtros.is_valid(raise_exception=True)
        canchas = listar_canchas(filtros.to_filtros())
        return Response(CanchaListSerializer(canchas, many=True).data)


class CanchaDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            cancha = obtener_cancha_publicada(pk)
        except Cancha.DoesNotExist:
            raise Http404
        return Response(CanchaDetailSerializer(cancha).data)


class DisponibilidadView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            cancha = obtener_cancha_publicada(pk)
        except Cancha.DoesNotExist:
            raise Http404

        query = DisponibilidadQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)

        horarios = horarios_disponibles(cancha, query.validated_data["fecha"])
        return Response(HorarioDisponibleSerializer(horarios, many=True).data)
