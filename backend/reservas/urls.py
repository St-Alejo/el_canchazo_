from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ReporteCanchaView, ReservaViewSet

router = DefaultRouter()
router.register("", ReservaViewSet, basename="reserva")

urlpatterns = [
    path("reporte/<int:cancha_id>/", ReporteCanchaView.as_view(), name="reservas-reporte-cancha"),
] + router.urls
