from django.core.management.base import BaseCommand
from loja.utils import processar_pedidos_expirados


class Command(BaseCommand):
    help = 'Process expired orders and restore stock'

    def handle(self, *args, **kwargs):
        self.stdout.write("Processing expired orders...")

        processar_pedidos_expirados()

        self.stdout.write(self.style.SUCCESS("Done!"))