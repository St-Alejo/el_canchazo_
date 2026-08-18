from urllib.parse import quote

from django.conf import settings

from .pagos import PuertoPagos


class AdaptadorPagosFalso(PuertoPagos):
    """Doble de pruebas: no llama a ningún servicio externo.

    `validar_firma_webhook` solo acepta el checksum fijo `CHECKSUM_VALIDO`, para poder
    simular tanto un webhook legítimo como uno con firma inválida en las pruebas.

    `crear_cobro` apunta a una página del propio frontend (`/pago-simulado/...`) que
    imita el checkout de Wompi: permite probar el flujo de reserva de punta a punta
    (Sprint 6) sin llaves de sandbox reales. El checksum va en la URL para que esa
    página pueda llamar al webhook con una firma "válida" — nunca se usa así con
    Wompi real, donde la firma la calcula y envía el servicio externo, no el navegador.
    """

    CHECKSUM_VALIDO = "firma-de-prueba-valida"

    def __init__(self):
        self.cobros_creados = []

    def crear_cobro(self, *, referencia, monto_total_centavos, descripcion, redirect_url):
        self.cobros_creados.append({"referencia": referencia, "monto_total_centavos": monto_total_centavos})
        url_pago = (
            f"{settings.FRONTEND_URL}/pago-simulado/{referencia}"
            f"?monto={monto_total_centavos}"
            f"&descripcion={quote(descripcion)}"
            f"&redirect={quote(redirect_url)}"
            f"&checksum={quote(self.CHECKSUM_VALIDO)}"
        )
        return {"referencia": referencia, "url_pago": url_pago}

    def validar_firma_webhook(self, payload):
        return (payload.get("signature") or {}).get("checksum") == self.CHECKSUM_VALIDO

    def extraer_confirmacion(self, payload):
        referencia = payload.get("referencia")
        estado = payload.get("estado")
        if not referencia or not estado:
            return None
        return {"referencia": referencia, "estado": estado}
