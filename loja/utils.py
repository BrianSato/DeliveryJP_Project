from loja.models import LoteProduto


def formatar_iene(valor):
    if valor is None:
        return'¥0'
    return f'¥{valor:,.0f}'

def criar_lote(produto,quantidade,data_validade):
    return LoteProduto.objects.create(
        produto=produto,
        quantidade=quantidade,
        data_validade=data_validade if data_validade else None
    )