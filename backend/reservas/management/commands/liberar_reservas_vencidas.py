from django.core.management.base import BaseCommand

from reservas.services import liberar_reservas_vencidas


class Command(BaseCommand):
    help = "Cancela las reservas pendiente_pago cuyo bloqueo temporal ya expiró sin pago confirmado."

    def handle(self, *args, **options):
        total = liberar_reservas_vencidas()
        self.stdout.write(self.style.SUCCESS(f"Reservas liberadas: {total}"))
