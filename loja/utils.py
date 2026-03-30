
def formatar_iene(valor):
    if valor is None:
        return'¥0'
    return f'¥{valor:,.0f}'

def criar_lote(produto,quantidade,data_validade):
    return produto.objects.create(
        produto=produto,
        quantidade=quantidade,
        data_validade=data_validade if data_validade else None
    )
def baixar_estoque(produto,quantidade):
    quantidade_restante = quantidade
    lotes = produto.lotes.filter(produto=produto).order_by('data_validade')

    for lote in lotes:
        if quantidade <= 0:
            break
        if lote.quantidade >= quantidade_restante:
            lote.quantidade -= quantidade_restante
            lote.save()
            break
        else:
            quantidade_restante -= lote.quantidade
            lote.quantidade = 0
            lote.save()
