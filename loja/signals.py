from datetime import date, timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ItemPedido, LoteProduto


@receiver(post_save, sender=ItemPedido)
def atualizar_status_e_estoque(sender, instance,created,**kwargs):

    valor_total = instance.valor_total_item()
    valor_pago = instance.valor_pago or 0
    status_anterior = None
    item_antigo = None

    if instance.pk and not created:
        item_antigo = ItemPedido.objects.get(pk=instance.pk)
        status_anterior = item_antigo.status_pagamento

    # atualiza status automaticamente e impôem data limite de pagamento
    # AGUARDANDO
    if valor_pago <= 0:
        instance.status_pagamento = 'AGUARDANDO'
        if status_anterior != 'AGUARDANDO':
            instance.data_limite_pagamento = date.today() + timedelta(days=1)
    # PARCIALMENTE PAGO
    elif valor_pago < valor_total:
        instance.status_pagamento = 'PARCIAL'
        if status_anterior != 'PARCIAL':
            instance.data_limite_pagamento = date.today() + timedelta(days=5)
    # TOTALMENTE PAGO
    else:
        instance.status_pagamento = 'PAGO'
        instance.data_limite_pagamento = None
    # CANCELAMENTO AUTOMÁTICO
    if (
            instance.data_limite_pagamento and
            date.today() > instance.data_limite_pagamento and
            instance.status_item != 'CANCELADO'
    ):
        instance.status_item = 'CANCELADO'
    # RETORNO AO ESTOQUE
    if (
            item_antigo and
            item_antigo.status_item != 'CANCELADO' and
            instance.status_item == 'CANCELADO' and
            instance.tipo == 'ESTOQUE' and
            instance.produto
    ):
        LoteProduto.objects.create(
            produto=self.produto,
            quantidade=self.quantidade,
        )
    # Salva as alterações se houver mudança
    instance.save(update_field=[
        'status_pagamento',
        'status_limite_pagamento',
        'status_item',
    ])
