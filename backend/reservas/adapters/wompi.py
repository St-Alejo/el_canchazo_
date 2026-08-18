import hashlib
import hmac
from urllib.parse import urlencode

import environ

from .pagos import PuertoPagos

env = environ.Env()


class AdaptadorWompi(PuertoPagos):
    """Web Checkout de Wompi (redirect + firma de integridad) y sus eventos de webhook
    (firma de checksum). No hace llamadas HTTP para "crear" el cobro: arma una URL
    firmada y Wompi se encarga del resto, avisando por webhook al confirmar el pago.

    Implementado a partir de la documentación pública de Wompi ("Web Checkout" y
    "Eventos"), sin llaves de sandbox disponibles en esta sesión para probarlo contra
    el servicio real — ver la nota en docs/AVANCE.md antes de usarlo en producción.
    """

    def __init__(self):
        self.llave_publica = env("WOMPI_LLAVE_PUBLICA")
        self.secreto_integridad = env("WOMPI_SECRETO_INTEGRIDAD")
        self.secreto_eventos = env("WOMPI_SECRETO_EVENTOS")
        self.url_checkout = env("WOMPI_URL_CHECKOUT", default="https://checkout.wompi.co/p/")

    def crear_cobro(self, *, referencia, monto_total_centavos, descripcion, redirect_url):
        cadena_integridad = f"{referencia}{monto_total_centavos}COP{self.secreto_integridad}"
        firma_integridad = hashlib.sha256(cadena_integridad.encode()).hexdigest()

        parametros = urlencode(
            {
                "public-key": self.llave_publica,
                "currency": "COP",
                "amount-in-cents": monto_total_centavos,
                "reference": referencia,
                "signature:integrity": firma_integridad,
                "redirect-url": redirect_url,
            }
        )
        return {"referencia": referencia, "url_pago": f"{self.url_checkout}?{parametros}"}

    def validar_firma_webhook(self, payload):
        firma = payload.get("signature") or {}
        propiedades = firma.get("properties", [])
        checksum_recibido = str(firma.get("checksum", ""))
        timestamp = payload.get("timestamp", "")
        datos = payload.get("data", {})

        valores = []
        for ruta in propiedades:
            valor = datos
            for parte in ruta.split("."):
                valor = valor.get(parte) if isinstance(valor, dict) else None
            valores.append("" if valor is None else str(valor))

        cadena = "".join(valores) + str(timestamp) + self.secreto_eventos
        checksum_calculado = hashlib.sha256(cadena.encode()).hexdigest()
        return hmac.compare_digest(checksum_calculado.upper(), checksum_recibido.upper())

    def extraer_confirmacion(self, payload):
        if payload.get("event") != "transaction.updated":
            return None
        transaccion = (payload.get("data") or {}).get("transaction") or {}
        referencia = transaccion.get("reference")
        estado = transaccion.get("status")
        if not referencia or not estado:
            return None
        return {"referencia": referencia, "estado": estado}
