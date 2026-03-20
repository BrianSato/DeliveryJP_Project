from datetime import date

from django.contrib import admin
from django.utils.html import mark_safe

from .models import Cliente, Produto, Venda, ItemVenda, Pagamento, LoteProduto, Encomenda
from loja.utils import formatar_iene


class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 1
    fields = ('produto','quantidade','preco_unitario','subtotal')
    readonly_fields = ('preco_unitario', 'subtotal') #mostra os valores calculados
    can_delete = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'produto':
            kwargs['queryset'] = Produto.objects.filter(
                ativo=True
            ).distinct()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class VendaAdmin(admin.ModelAdmin):
    inlines = [ItemVendaInline]
    list_display = (
        'cliente',
        'valor_total_formatado',
        'valor_pago_formatado',
        'status',
        'tipo_venda',
        'data_venda_formatada',
        'data_limite_formatada'
    )
    readonly_fields = ('data_venda',)
    search_fields = ('cliente__nome',)
    def get_fields(self, request, obj=None):
        #quando esta criando uma venda
        if obj is None:
            return(
                'cliente',
                'tipo_venda',
                'status',
                'data_limite_pagamento',
            )
        #quando esta editando uma venda existente
        return(
            'cliente',
            'tipo_venda',
            'status',
            'data_venda',
            'data_limite_pagamento',
            'valor_pago',
            'valor_total',

        )
    def data_venda_formatada(self,obj):
        if obj.data_venda:
            return obj.data_venda.strftime('%d/%m/%Y')
        return '-'
    data_venda_formatada.short_description = 'Data da Venda'
    def data_limite_formatada(self,obj):
        if obj.data_limite_pagamento:
            return obj.data_limite_pagamento.strftime('%d/%m/%Y')
        return '-'
    data_limite_formatada.short_description = 'Data de Limite de Pagamento'
    def valor_total_formatado(self,obj):
        return formatar_iene(obj.valor_total)
    valor_total_formatado.short_description = 'Valor Total'
    def valor_pago_formatado(self,obj):
        return formatar_iene(obj.valor_pago)
    valor_pago_formatado.short_description = 'Valor Pago'

class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome','telefone','saldo_atual','proxima_data_limite','pontos')
    search_fields = ('telefone','nome')

    def proxima_data_limite(self,obj):
        venda = obj.venda_set.filter(
            status__in=['PENDENTE','PARCIAL','PAGO','CANCELADO']
        ).order_by('data_limite_pagamento').first()
        if venda and venda.data_limite_pagamento:
            return venda.data_limite_pagamento.strftime('%d/%m/%Y')
        return '-'
    proxima_data_limite.short_description = 'Data de Limite de Pagamento'

    def saldo_atual(self,obj):
        total =  obj.saldo_devedor
        return formatar_iene(total)
    saldo_atual.short_description = 'Saldo Devedor'

class LoteProdutoInline(admin.TabularInline):
    model = LoteProduto
    extra = 0
    fields = ('quantidade','data_validade','status_colorido')
    readonly_fields = ('status_colorido',)

    def status_colorido(self, obj):
        if not obj.pk:
            return ''

        status = obj.status_lote()

        if status == 'VENCIDO':
            return mark_safe('<span style="color:red;font-weight:bold;">•Vencidos</span>')
        if status == 'VENCIMENTO_PROXIMO':
            return mark_safe('<span style="color:yellow;font-weight:bold;">•Vencimento Próximo</span>')
        if status == 'SEM_VALIDADE':
            return mark_safe('<span style="color:gray;font-weight:bold;">•Sem validade</span>')
        return mark_safe('<span style="color:green;font-weight:bold;">•OK</span>')

    status_colorido.short_description = 'Status Validade'

    class Media:
        js = ('loja/js/validade_alerta.js',)

class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        'nome_produto',
        'preco_formatado',
        'estoque_total',
        'total_encomendados',
        'ativo','status_colorido'
    )
    search_fields = ('nome_produto',)
    inlines = [LoteProdutoInline]

    def status_colorido(self,obj):
        status = obj.status_validade()

        if status == 'VENCIDO':
            return mark_safe('<span style="color:red;font-weight:bold;">•Alguns produtos vencidos</span>')
        if status == 'VENCIMENTO_PROXIMO':
            return mark_safe('<span style="color:yellow;font-weight:bold;">•Produtos à vencer</span>')
        if status == 'SEM_VALIDADE':
            return mark_safe('<span style="color:gray;font-weight:bold;">•Sem validade</span>')
        return mark_safe('<span style="color:green;font-weight:bold;">•OK</span>')

    status_colorido.short_description = 'Status Validade'

    def preco_formatado(self,obj):
        return formatar_iene(obj.preco_unitario)
    preco_formatado.short_description = 'Preco Unitário'

class EncomendaAdmin(admin.ModelAdmin):
    list_display = (
        'cliente',
        'produto',
        'valor_total_formatado',
        'valor_pago_formatado',
        'status_pagamento_colorido',
        'status_encomenda_colorido',
        'data_encomenda',
    )
    fields = (
        'cliente',
        'produto',
        'quantidade',
        'valor_total',
        'valor_pago',
        'status_pagamento',
        'status',
        'data_encomenda',
    )
    readonly_fields = ('valor_total','data_encomenda')
    list_filter = ('status','status_pagamento')
    search_fields = ('cliente__nome','produto__nome_produto')

    def valor_total_formatado(self,obj):
        return formatar_iene(obj.valor_total)
    valor_total_formatado.short_description = 'Valor Total'

    def valor_pago_formatado(self,obj):
        return formatar_iene(obj.valor_pago)
    valor_pago_formatado.short_description = 'Valor Pago'

    def status_pagamento_colorido(self,obj):

        if obj.status_pagamento == 'AGUARDANDO':
            return mark_safe('<span style="color:red;font-weight:bold;">Aguardando Pagamento</span>')
        elif obj.status_pagamento == 'PARCIAL':
            return mark_safe('<span style="color:orange;font-weight:bold;">Pagamento Parcial</span>')
        return mark_safe('<span style="color:green;font-weight:bold;">Pagol</span>')

    status_pagamento_colorido.short_description = 'Status Pagamento'

    def status_encomenda_colorido(self, obj):

        if obj.status == 'PENDENTE':
            return mark_safe('<span style="color:gray;font-weight:bold;">Aguardando Pedido</span>')
        elif obj.status == 'PEDIDO':
            return mark_safe('<span style="color:blue;font-weight:bold;">Pedido Realizado</span>')
        elif obj.status == 'CHEGOU':
            return mark_safe('<span style="color:purple;font-weight:bold;">Pedido Chegou</span>')
        elif obj.status == 'ENVIADO':
            return mark_safe('<span style="color:orange;font-weight:bold;">Pedido Enviado</span>')
        elif obj.status == 'ENTREGUE':
            return mark_safe('<span style="color:green;font-weight:bold;">Pedido Entregue</span>')

        return mark_safe('<span style="color:red;font-weight:bold;">Cancelado</span>')

    status_encomenda_colorido.short_description = 'Status Encomenda'

class PagamentoAdmin(admin.ModelAdmin):
    list_display = ('get_cliente','valor_total','forma_pagamento','status','data_limite_formatada')
    search_fields = ('venda__cliente__nome','venda__cliente__telefone')
    list_filter = ('venda__status','venda__forma_pagamento')

    def get_cliente(self,obj):
        return obj.venda.cliente.nome
    get_cliente.admin_order_field = 'venda__cliente__nome'
    get_cliente.short_description = 'Cliente'
    def valor_total(self,obj):
        return formatar_iene(obj.venda.valor_total)
    valor_total.short_description = 'Valor Total'
    def forma_pagamento(self,obj):
        return obj.venda.forma_pagamento
    forma_pagamento.short_description = 'Forma de Pagamento'
    def status(self,obj):
        return obj.venda.status
    status.short_description = 'Status'
    def data_limite_formatada(self, obj):
        if obj.venda.data_limite_pagamento:
            return obj.venda.data_limite_pagamento.strftime('%d/%m/%Y')
        return '-'
    data_limite_formatada.short_description = 'Data de Limite de Pagamento'


admin.site.register(Cliente,ClienteAdmin)
admin.site.register(Produto,ProdutoAdmin)
admin.site.register(Encomenda,EncomendaAdmin)
admin.site.register(Venda,VendaAdmin)
admin.site.register(ItemVenda)
admin.site.register(Pagamento,PagamentoAdmin)

