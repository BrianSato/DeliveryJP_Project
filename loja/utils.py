import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

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
    lotes = produto.lotes.filter(ativo=True).order_by('data_validade','id')
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

            quantidade_restante -= quantidade_usada

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

def devolver_parcial_estoque(item_pedido, quantidade):
    restante = quantidade

    for registro in item_pedido.lotes.all():
        if restante <= 0:
            break

        lote = registro.lote

        devolver = min(registro.quantidade, restante)

        lote.quantidade += devolver
        lote.save()

        registro.quantidade -= devolver
        registro.save()

        restante -= devolver

def processar_expiracao_pedido(pedido):
    if pedido.status != 'ABERTO':
        return

    if not pedido.esta_expirado:
        return

    if pedido.status_pagamento == 'PAGO':
        return

    for item in pedido.itens.all():
        if item.tipo == 'ESTOQUE':
            devolver_estoque(item)

    pedido.status = 'EXPIRADO'
    pedido.save()

def processar_pedidos_expirados():
    from loja.models import Pedido

    pedidos = Pedido.objects.filter(status='ABERTO')

    for pedido in pedidos:
        processar_expiracao_pedido(pedido)