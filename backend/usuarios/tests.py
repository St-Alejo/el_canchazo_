from rest_framework import status
from rest_framework.test import APITestCase

from .models import Usuario


class RegistroTests(APITestCase):
    url = "/api/usuarios/registro/"

    def datos_validos(self, **overrides):
        datos = {
            "username": "juanp",
            "email": "juan@example.com",
            "celular": "3001234567",
            "password": "clave-segura-123",
            "rol": Usuario.ROL_JUGADOR,
            "consentimiento_datos_aceptado": True,
        }
        datos.update(overrides)
        return datos

    def test_registro_exitoso_crea_usuario_y_devuelve_tokens(self):
        respuesta = self.client.post(self.url, self.datos_validos(), format="json")

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", respuesta.data)
        self.assertIn("refresh", respuesta.data)

        usuario = Usuario.objects.get(celular="3001234567")
        self.assertTrue(usuario.check_password("clave-segura-123"))
        self.assertTrue(usuario.consentimiento_datos_aceptado)
        self.assertIsNotNone(usuario.fecha_consentimiento)

    def test_registro_sin_consentimiento_falla(self):
        respuesta = self.client.post(
            self.url, self.datos_validos(consentimiento_datos_aceptado=False), format="json"
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Usuario.objects.filter(celular="3001234567").exists())

    def test_registro_no_permite_autoasignar_superadmin(self):
        respuesta = self.client.post(
            self.url, self.datos_validos(rol=Usuario.ROL_SUPERADMIN), format="json"
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    url = "/api/usuarios/login/"

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="mariaj",
            email="maria@example.com",
            celular="3009876543",
            password="clave-segura-123",
            rol=Usuario.ROL_JUGADOR,
            consentimiento_datos_aceptado=True,
        )

    def test_login_por_celular(self):
        respuesta = self.client.post(
            self.url, {"identificador": "3009876543", "password": "clave-segura-123"}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIn("access", respuesta.data)

    def test_login_por_correo(self):
        respuesta = self.client.post(
            self.url, {"identificador": "maria@example.com", "password": "clave-segura-123"}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIn("access", respuesta.data)

    def test_login_con_password_incorrecta_falla(self):
        respuesta = self.client.post(
            self.url, {"identificador": "3009876543", "password": "incorrecta"}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_endpoint_yo_requiere_autenticacion(self):
        respuesta = self.client.get("/api/usuarios/yo/")
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_endpoint_yo_con_token_devuelve_usuario(self):
        login = self.client.post(
            self.url, {"identificador": "3009876543", "password": "clave-segura-123"}, format="json"
        )
        access = login.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        respuesta = self.client.get("/api/usuarios/yo/")

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["celular"], "3009876543")
