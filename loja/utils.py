from django.utils import timezone

def formatar_iene(valor):
    if valor is None:
        return'¥0'
    return f'¥{valor:,.0f}'

def criar_lote(produto,quantidade,data_validade):
    from loja.models import LoteProduto
    return LoteProduto.objects.create(
        produto=produto,
        quantidade=quantidade,
        data_validade=data_validade if data_validade else None
    )
def baixar_estoque(produto,quantidade,item_pedido):
    print("BAIXANDO ESTOQUE...")
    from loja.models import ItemPedidoLote
    quantidade_restante = quantidade
    lotes = produto.lotes.filter(produto=produto).order_by('data_validade')

    for lote in lotes:
        if quantidade_restante <= 0:
            break
        if lote.quantidade >= quantidade_restante:
            lote.quantidade -= quantidade_restante
            lote.save()

            ItemPedidoLote.objects.create(
                item_pedido=item_pedido,
                lote=lote,
                quantidade=quantidade_restante
            )

            break
        else:
            quantidade_usada = lote.quantidade

            ItemPedidoLote.objects.create(
                item_pedido=item_pedido,
                lote=lote,
                quantidade=quantidade_usada
            )

            quantidade_restante -= lote.quantidade_usada
            lote.quantidade = 0
            lote.save()

def devolver_estoque(item_pedido):
    if hasattr(item_pedido, '_estoque_devolvido'):
        return

    for registro in item_pedido.lotes.all():
        lote = registro.lote
        lote.quantidade += registro.quantidade
        lote.save()

    item_pedido._estoque_devolvido = True

def processar_expiracao_pedido(pedido):
    if pedido.status != 'ATIVO':
        return

    if pedido.data_limite_pagamento >= timezone.now().date():
        return

    if pedido.status_pagamento == 'PAGO':
        return  # não expira pedido pago

    for item in pedido.itens.all():
        devolver_estoque(item)

    pedido.status = 'EXPIRADO'
    pedido.save()

def processar_pedidos_expirados():
    from loja.models import Pedido
    pedidos = Pedido.objects.filter(status='ATIVO')

    for pedido in pedidos:
        processar_expiracao_pedido(pedido)