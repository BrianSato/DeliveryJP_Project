from django.utils import timezone
from .utils import processar_pedidos_expirados


class ProcessarPedidosExpiradosMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.last_run = None  # controle interno

    def __call__(self, request):
        agora = timezone.now()

        # roda apenas a cada 5 minutos
        if not self.last_run or (agora - self.last_run).seconds > 300:
            processar_pedidos_expirados()
            self.last_run = agora

        response = self.get_response(request)
        return response