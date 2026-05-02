from .utils import get_pedidos_para_analise

def pedidos_para_analise(request):
    pedidos = get_pedidos_para_analise()

    return {
        'pedidos_para_analise_count': len(pedidos)
    }