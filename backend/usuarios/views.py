from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer, RegistroSerializer, UsuarioSerializer
from .services import registrar_usuario


def _tokens_para(usuario):
    refresh = RefreshToken.for_user(usuario)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


class RegistroView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = registrar_usuario(serializer.validated_data)
        return Response(
            {"usuario": UsuarioSerializer(usuario).data, **_tokens_para(usuario)},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        usuario = serializer.validated_data["usuario"]
        return Response({"usuario": UsuarioSerializer(usuario).data, **_tokens_para(usuario)})


class YoView(generics.RetrieveAPIView):
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
