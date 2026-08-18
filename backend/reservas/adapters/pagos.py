from abc import ABC, abstractmethod


class PuertoPagos(ABC):
    """Interfaz del proveedor de pagos. Wompi es la única implementación real hoy,
    pero `services.py` y `views.py` solo conocen esta interfaz — nunca a Wompi directo.
    """

    @abstractmethod
    def crear_cobro(self, *, referencia, monto_total_centavos, descripcion, redirect_url):
        """Devuelve {"referencia": str, "url_pago": str} para redirigir al jugador a pagar."""

    @abstractmethod
    def validar_firma_webhook(self, payload):
        """True si el evento realmente viene del proveedor de pagos."""

    @abstractmethod
    def extraer_confirmacion(self, payload):
        """Devuelve {"referencia": str, "estado": str} o None si el evento no aplica."""
