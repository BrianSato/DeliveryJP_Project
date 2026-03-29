from xml.etree.ElementInclude import default_loader

from django.core.exceptions import ValidationError
from django.db import models
from datetime import date, timedelta

from django.utils.safestring import mark_safe


#===================== CLIENTES =========================
class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20, unique=True)
    endereco = models.CharField(max_length=200)
    pontos = models.IntegerField(default=0)
    validade_pontos = models.DateField(blank=True,null=True)
    data_cadastro = models.DateField(auto_now_add=True)

    @property
    def proxima_data_limite(self):
        #Pega todos os pedidos do cliente
        item = ItemPedido.objects.filter(
            pedido__cliente=self,
            data_limite_pagamento__isnull=False,
            status_item__in=['PENDENTE','PEDIDO','CHEGOU','ENVIADO','ENTREGUE','CANCELADO']
        ).order_by('data_limite_pagamento').first()

        return item.data_limite_pagamento if item else None

    @property
    def saldo_devedor(self):
        itens = ItemPedido.objects.filter(
            pedido__cliente = self,
            status_pagamento__in=['PENDENTE','PARCIAL']
        ).order_by('status_pagamento')

        return sum(i._item() - (i.valor_pago or 0) for i in itens)

    @property
    def total_gasto(self):
        itens = ItemPedido.objects.filter(
            pedido__cliente = self,
            status_pagamento = 'PAGO'
        )
        return sum(i.valor_total_item() for i in itens)

    @property
    def tem_atraso(self):
        return ItemPedido.objects.filter(
            pedido__cliente = self,
            data_limite_pagamento__lt=date.today(),
            status_pagamento__in=['AGUARDANDO','PARCIAL']
        ).exists()

    def __str__(self):
        return self.nome

#===================== PRODUTO =========================

class Produto(models.Model):
    nome_produto = models.CharField(max_length=100)
    preco_unitario = models.DecimalField(max_digits=10,decimal_places=2)
    ativo = models.BooleanField(default=True)

    @property
    def estoque_total(self):
        return sum(lote.quantidade for lote in self.loteproduto_set.all())

    def total_encomendados(self):
        return self.itens_pedido.filter(
            tipo='ENCOMENDA',
            status_item__in=['PEDIDO','ENVIADO','CHEGOU','ENTREGUE']
        ).aggregate(
            total=models.Sum('quantidade')
        )['total'] or 0

    def status_validade(self):
        lotes = self.loteproduto_set.all()
        if not lotes.exists():
            return "SEM_VALIDADE"
        hoje = date.today()

        tem_vencido = False
        tem_vencimento_proximo = False

        for lote in lotes:
            if not lote.data_validade:
                continue
            if lote.data_validade < hoje:
                tem_vencido = True
            elif(lote.data_validade - hoje).days <= 7:
                tem_vencimento_proximo = True

        if tem_vencido:
            return 'VENCIDO'
        if tem_vencimento_proximo:
            return 'VENCIMENTO_PROXIMO'
        return 'OK'

    def status_validade_colorido(self):
        status = self.status_validade()

        if status == 'VENCIDO':
            return mark_safe('<span style="color:red;font-weight:bold;">•Alguns produtos vencidos</span>')
        if status == 'VENCIMENTO_PROXIMO':
            return mark_safe('<span style="color:orange;font-weight:bold;">•Produtos à vencer</span>')
        if status == 'SEM_VALIDADE':
            return mark_safe('<span style="color:gray;font-weight:bold;">•Sem validade</span>')
        return mark_safe('<span style="color:green;font-weight:bold;">•OK</span>')

    def __str__(self):
        return self.nome_produto

#===================== LOTE PRODUTO =========================

class LoteProduto(models.Model):
    produto = models.ForeignKey(Produto,on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    data_validade = models.DateField(null=True,blank=True)


    def status_lote(self):
        if not self.data_validade:
            return 'SEM_VALIDADE'

        hoje = date.today()
        if self.data_validade < hoje:
            return 'VENCIDO'
        elif (self.data_validade - hoje).days <= 7:
            return 'VENCIMENTO_PROXIMO'
        return 'OK'

    def status_lote_colorido(self):
        if not self.pk:
            return ''

        status = self.status_lote()

        if status == 'VENCIDO':
            return mark_safe('<span style="color:red;font-weight:bold;">•Vencidos</span>')
        if status == 'VENCIMENTO_PROXIMO':
            return mark_safe('<span style="color:orange;font-weight:bold;">•Vencimento Próximo</span>')
        if status == 'SEM_VALIDADE':
            return mark_safe('<span style="color:gray;font-weight:bold;">•Sem validade</span>')
        return mark_safe('<span style="color:green;font-weight:bold;">•OK</span>')

    def __str__(self):
        return f'{self.produto} - {self.quantidade} unidades - Validade: {self.data_validade}'

#===================== PEDIDO =========================

class Pedido(models.Model):

    FORMA_PAGAMENTO = [
        ('DINHEIRO', 'Dinheiro'),
        ('CARTAO', 'Cartão'),
        ('TRANSFERENCIA', 'Transferência'),
    ]

    cliente = models.ForeignKey(Cliente,on_delete=models.CASCADE)
    data_pedido = models.DateField(auto_now_add=True)
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    forma_pagamento = models.CharField(max_length=15, choices=FORMA_PAGAMENTO, null=True, blank=True)
    data_limite_pagamento = models.DateField(null=True, blank=True)

    @property
    def valor_total(self):
        return sum(item.valor_total_item() for item in self.itens.all())

    @property
    def valor_restante(self):
        return self.valor_total - self.valor_pago

    @property
    def status_pagamento(self):

        if self.valor_pago == 0:
            return 'AGUARDANDO'
        elif self.valor_pago < self.valor_total:
            return 'PARCIAL'
        else:
            return 'PAGO'
    def atualizar_data_limite(self):
        if self.valor_pago == 0:
            self.data_limite_pagamento = date.today() + timedelta(days=1)
        elif self.valor_pago < self.valor_total:
            self.data_limite_pagamento = date.today() + timedelta(days=5)
        else:
            self.data_limite_pagamento = None

    def __str__(self):
        return f'Pedido:{self.cliente}'

#===================== ITEM PEDIDO =========================

class ItemPedido(models.Model):
    TIPO_VENDA=[
        ('ESTOQUE','Estoque'),
        ('ENCOMENDA','Encomenda') ,
    ]
    STATUS_ITEM = [
        ('PENDENTE', 'Aguardando Pedido'),
        ('PEDIDO', 'Pedido feito'),
        ('CHEGOU', 'Produto chegou'),
        ('ENVIADO', 'Enviado'),
        ('ENTREGUE', 'Entregue ao cliente'),
        ('CANCELADO', 'Cancelado')
    ]

    pedido = models.ForeignKey(Pedido,on_delete=models.CASCADE,related_name='itens')
    produto = models.ForeignKey(Produto,on_delete=models.SET_NULL,null=True,blank=True,related_name='itens_pedido')
    nome_produto = models.CharField(max_length=100, null=True,blank=True)
    tipo = models.CharField(max_length=15,choices=TIPO_VENDA)
    quantidade = models.IntegerField(default=0)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    status_item = models.CharField(max_length=15,choices=STATUS_ITEM,default='PENDENTE')

    def valor_total_item(self):
        return self.valor_unitario * self.quantidade

    def clean(self):
        # DEVE TER PRODUTO OU NOME_PRODUTO
        if not self.produto and not self.nome_produto:
            raise ValidationError('Informe um produto ou nome do produto')
        #NÃO PODE TER OS DOIS AO MESMO TEMPO
        if self.produto and self.nome_produto:
            raise ValidationError('Escolha produto OU nome do produto')
        #QUANTIDADE OBRIGATÓRIA E VÁLIDA
        if not self.quantidade or self.quantidade <=0:
            raise ValidationError('Quantidade deve ser maior que zero')
        #TIPO ESTOQUE PRECISA DE PRODUTO
        if self.tipo == 'ESTOQUE' and not self.produto:
            raise ValidationError('Selecione um produto para itens de estoque')
        #TIPO ENCOMENDA PRECISA DE NOME
        if self.tipo == 'ENCOMENDA' and not self.nome_produto:
            raise ValidationError('Informe o nome do produto para encomenda')

    def save(self,*args,**kwargs):
        item_antigo = None

        if self.pk:
            try:
                item_antigo = ItemPedido.objects.get(pk=self.pk)
                status_anterior = item_antigo.status_pagamento
            except ItemPedido.DoesNotExist:
                pass

        # RETORNO AO ESTOQUE
        if (
                item_antigo and
                item_antigo.status_item != 'CANCELADO' and
                self.status_item == 'CANCELADO' and
                self.tipo == 'ESTOQUE' and
                self.produto and
                self.quantidade
        ):
            LoteProduto.objects.create(
                produto=self.produto,
                quantidade=self.quantidade,
            )

        self.full_clean()
        super().save(*args,**kwargs)
    def __str__(self):
        if self.produto:
            return f'{self.produto.nome_produto} - {self.quantidade}'
        return f'{self.nome_produto} ({self.quantidade}x)'



