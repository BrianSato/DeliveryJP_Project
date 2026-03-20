from django.core.management.base import BaseCommand
from datetime import date
from loja.models import Encomenda

class Command(BaseCommand):
    help = 'Cancela encomenda com pagamento vencido'

    def handle(self, *args, **options):
        encomendas = Encomenda.objects.filter(
            data_limite_pagamento__lt=date.today(),
            status__in=['PENDENTE','PEDIDO']
        )
        total = encomendas.count()

        for e in encomendas:
            e.status = 'CANCELADO'
            e.save()

        self.stdout.write(
            self.style.SUCCESS(f'{total} encomendas canceladas com sucesso!'))