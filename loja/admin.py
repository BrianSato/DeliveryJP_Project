from datetime import date

from django.contrib import admin
from django.utils.html import mark_safe

from .models import Cliente, Produto, LoteProduto,Pedido, ItemPedido
from loja.utils import formatar_iene

#===================== CLIENTES =========================

class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'telefone',
        'saldo_atual',
        'proxima_data_limite',
        'tem_atraso_colorido',
        'pontos')
    search_fields = ('telefone','nome')

    def proxima_data_limite(self,obj):
        data = obj.proxima_data_limite
        if data:
            return data.strftime('%d/%m/%Y')
        return '-'
    proxima_data_limite.short_description = 'Próx. Data Limite'

    def saldo_atual(self,obj):
        total =  obj.saldo_devedor_total
        return formatar_iene(total or 0)
    saldo_atual.short_description = 'Saldo Devedor'

    def tem_atraso_colorido(self,obj):
        if obj.tem_atraso():
            return mark_safe('<span style= "color:red;font-weight:bold;"> ⚠️ Atrasado</span>')
        return mark_safe('<span style= "color:green;font-weight:bold;"> ✅️ Em dia</span>')
    tem_atraso_colorido.short_description = 'Situação'

#===================== ITEM PEDIDO =========================

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1
    fields = (
        'produto',
        'nome_produto',
        'valor_unitario',
        'tipo',
        'quantidade',
    )

    readonly_fields = (
        'valor_unitario_formatado',
        'valor_pago_formatado',
        'status_pagamento_colorido',
        )

    can_delete = True

    def valor_unitario_formatado(self,obj):
        return formatar_iene(obj.valor_unitario)
    valor_unitario_formatado.short_description = 'Valor Unitário'
    def valor_pago_formatado(self,obj):
        return formatar_iene(obj.pedido.valor_pago)
    valor_pago_formatado.short_description = 'Valor Pago'

    def status_pagamento_colorido(self,obj):
        if obj.pedido.status_pagamento == 'AGUARDANDO':
            return mark_safe('<span style="color:red;font-weight:bold;">Aguardando Pagamento</span>')
        elif obj.pedido.status_pagamento == 'PARCIAL':
            return mark_safe('<span style="color:orange;font-weight:bold;">Pagamento Parcial</span>')
        return mark_safe('<span style="color:green;font-weight:bold;">Pago</span>')

    status_pagamento_colorido.short_description = 'Status Pagamento'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'produto':
            kwargs['queryset'] = Produto.objects.filter(
                ativo=True
            ).distinct()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    def save_models(self, request, obj, form, formset, change):
        print('ITEM SALVO',obj)
        print('PEDIDO RELACIONADO',obj.pedido)
        super().save_model(request,obj,change)

#===================== PEDIDO ========================

class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        'cliente',
        'valor_total_formatado',
        'valor_pago_formatado',
        'data_pedido_formatada',
        'data_limite_formatada',
        'status_pagamento_display',
        'status_encomenda_colorido',
    )
    inlines = [ItemPedidoInline]
    readonly_fields = ('data_pedido','valor_total_formatado',)
    search_fields = ('cliente__nome',)

    def get_fields(self, request, obj=None):
        return (
            'cliente',
            'data_pedido',
            'data_limite_pagamento',
        )

    def data_pedido_formatada(self,obj):
        if obj.data_pedido:
            return obj.data_pedido.strftime('%d/%m/%Y')
        return '-'
    data_pedido_formatada.short_description = 'Data do Pedido'

    def data_limite_formatada(self,obj):
        if obj.data_limite_pagamento:
            return obj.data_limite_pagamento.strftime('%d/%m/%Y')
        return '-'
    data_limite_formatada.short_description = 'Data de Limite de Pagamento'

    def status_encomenda_colorido(self, obj):
        if obj.status_encomenda == 'PENDENTE':
            return mark_safe('<span style="color:gray;font-weight:bold;">Aguardando Pedido</span>')
        elif obj.status_encomenda == 'PEDIDO':
            return mark_safe('<span style="color:blue;font-weight:bold;">Pedido Realizado</span>')
        elif obj.status_encomenda == 'CHEGOU':
            return mark_safe('<span style="color:purple;font-weight:bold;">Pedido Chegou</span>')
        elif obj.status_encomenda == 'ENVIADO':
            return mark_safe('<span style="color:orange;font-weight:bold;">Pedido Enviado</span>')
        elif obj.status_encomenda == 'ENTREGUE':
            return mark_safe('<span style="color:green;font-weight:bold;">Pedido Entregue</span>')

        return mark_safe('<span style="color:red;font-weight:bold;">Cancelado</span>')
    status_encomenda_colorido.short_description = 'Status Item'

    def status_pagamento_display(self, obj):
        return obj.status_pagamento

    status_pagamento_display.short_description = 'Pagamento'

    def valor_total_formatado(self,obj):
        return formatar_iene(obj.valor_total)
    valor_total_formatado.short_description = 'Valor Total'
    def valor_pago_formatado(self,obj):
        return formatar_iene(obj.valor_pago)
    valor_pago_formatado.short_description = 'Valor Pago'
    def get_queryset(self,request):
        return super().get_queryset(request).prefetch_related('itens')


#===================== LOTE PRODUTO =========================

class LoteProdutoInline(admin.TabularInline):
    model = LoteProduto
    extra = 0
    fields = ('quantidade','data_validade','status_colorido')
    readonly_fields = ('status_colorido',)

    def status_colorido(self, obj):
        return obj.status_lote_colorido()

    status_colorido.short_description = 'Status Validade'

    class Media:
        js = ('loja/js/validade_alerta.js',)

#===================== PRODUTO =========================

class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        'nome_produto',
        'preco_formatado',
        'estoque_disponivel',
        'total_encomendados',
        'ativo','status_val_colorido'
    )
    search_fields = ('nome_produto',)
    inlines = [LoteProdutoInline]

    def status_val_colorido(self,obj):
        return obj.status_validade_colorido()

    status_val_colorido.short_description = 'Status Validade'

    def preco_formatado(self,obj):
        return formatar_iene(obj.preco_unitario)
    preco_formatado.short_description = 'Preco Unitário'

admin.site.register(Cliente,ClienteAdmin)
admin.site.register(Produto,ProdutoAdmin)
admin.site.register(Pedido,PedidoAdmin)
admin.site.register(ItemPedido)


