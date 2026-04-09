from django.utils import timezone
from django.core.cache import cache
from loja.utils import processar_pedidos_expirados

class ProcessarPedidosExpiradosMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        agora = timezone.now()

        # pega última execução do cache
        ultima_execucao = cache.get('ultima_execucao_expiracao')

        # executa a cada 5 minutos
        if not ultima_execucao or (agora - ultima_execucao).total_seconds() > 300:

            print(" Executando verificação de pedidos expirados...")

            processar_pedidos_expirados()

            # salva no cache por 5 minutos
            cache.set('ultima_execucao_expiracao', agora, timeout=300)

        response = self.get_response(request)
        return response