from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, RegistroView, YoView

urlpatterns = [
    path("registro/", RegistroView.as_view(), name="usuarios-registro"),
    path("login/", LoginView.as_view(), name="usuarios-login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="usuarios-token-refresh"),
    path("yo/", YoView.as_view(), name="usuarios-yo"),
]
