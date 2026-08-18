from django.urls import path

from .views import CanchaDetailView, CanchaListView, DisponibilidadView

urlpatterns = [
    path("", CanchaListView.as_view(), name="canchas-lista"),
    path("<int:pk>/", CanchaDetailView.as_view(), name="canchas-detalle"),
    path("<int:pk>/disponibilidad/", DisponibilidadView.as_view(), name="canchas-disponibilidad"),
]
