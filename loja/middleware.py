from django.utils import timezone
from django.core.cache import cache
from .utils import processar_pedidos_expirados


class ProcessarPedidosExpiradosMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        agora = timezone.now()

        # pega última execução do cache
        ultima_execucao = cache.get('ultima_execucao_expiracao')

        # verifica se já passou 5 minutos
        if not ultima_execucao or (agora - ultima_execucao).seconds > 300:
            processar_pedidos_expirados()

            # salva no cache com timeout de 5 minutos
            cache.set('ultima_execucao_expiracao', agora, timeout=300)

        response = self.get_response(request)
        return response