
from django.core.exceptions import ValidationError
from django.db import models
from datetime import date, timedelta

from django.db.models import Sum
from django.utils.safestring import mark_safe
from loja.utils import baixar_estoque

#==================== CONSTANTES =======================
VALOR_POR_PONTO = 1000
PONTOS_POR_CUPOM = 50
VALOR_CUPOM = 1000
#===================== CLIENTES =========================
class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20, unique=True)
    endereco = models.CharField(max_length=200)
    pontos = models.IntegerField(default=0)
    cupons = models.IntegerField(default=0)
    validade_pontos = models.DateField(blank=True,null=True)
    data_cadastro = models.DateField(auto_now_add=True)

    @property
    def telefone_formatado(self):

        if self.telefone and len(self.telefone) == 11:
            return f"{self.telefone[:3]}-{self.telefone[3:7]}-{self.telefone[7:]}"

        return self.telefone

    @property
    def proxima_data_limite(self):
       pedidos= self.pedidos.exclude(data_limite_pagamento=None)
       if pedidos.exists():
           return min(p.data_limite_pagamento for p in pedidos)
       return None

    @property
    def saldo_devedor_total(self):
        return sum(pedido.valor_restante or 0 for pedido in self.pedidos.all())

    @property
    def total_gasto(self):
        itens = ItemPedido.objects.filter(
            pedido__cliente = self,
        )
        return sum(i.valor_total_item() for i in itens)

    def tem_atraso(self):
        for pedido in self.pedidos.all():
            if(
                pedido.data_limite_pagamento and
                pedido.data_limite_pagamento < date.today() and
                pedido.status_pagamento != 'PAGO'
            ):
                return True
        return False

    def save(self,*args,**kwargs):
        if self.telefone:
            self.telefone = self.telefone.replace('-','')
        super().save(*args,**kwargs)

    def __str__(self):
        return self.nome

#===================== PRODUTO =========================

class Produto(models.Model):
    nome_produto = models.CharField(max_length=100)
    preco_unitario = models.DecimalField(max_digits=10,decimal_places=2)
    ativo = models.BooleanField(default=True)

    @property
    def estoque_disponivel(produto):
        return produto.lotes.aggregate(total=Sum('quantidade'))['total'] or 0

    def total_encomendados(self):
        return self.itens_pedido.filter(
            tipo='ENCOMENDA',
        ).aggregate(
            total=models.Sum('quantidade')
        )['total'] or 0

    def status_validade(self):
        lotes = self.lotes.all()

        if not lotes.exists() or lotes.count() == 0:
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
    produto = models.ForeignKey(Produto,on_delete=models.CASCADE,related_name='lotes')
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
    STATUS_ENCOMENDA = [
        ('PENDENTE', 'Aguardando Pedido'),
        ('PEDIDO', 'Pedido feito'),
        ('CHEGOU', 'Produto chegou'),
        ('ENVIADO', 'Enviado'),
        ('ENTREGUE', 'Entregue ao cliente'),
        ('CANCELADO', 'Cancelado')
    ]
    cliente = models.ForeignKey(Cliente,on_delete=models.CASCADE, related_name='pedidos')
    data_pedido = models.DateField(auto_now_add=True)
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    forma_pagamento = models.CharField(max_length=15, choices=FORMA_PAGAMENTO, null=True, blank=True)
    data_limite_pagamento = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('ABERTO','Aberto'),('FECHADO','Fechado')], default='ABERTO')
    status_pag = models.CharField(
        max_length=20,
        choices=[('ATIVO','Ativo'),
                 ('EXPIRADO','Expirado'),
                 ('CANCELADO','Cancelado')
                 ],
        default='ATIVO'
    )
    status_encomenda = models.CharField(max_length=15, choices=STATUS_ENCOMENDA, default='PENDENTE')
    pontos_creditados = models.BooleanField(default=False)
    cupom_usado = models.BooleanField(default=False)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def valor_total(self):
        total =  sum(item.valor_total_item() for item in self.itens.all())
        return max(total - self.desconto, 0)

    @property
    def valor_restante(self):
        if self.valor_pago > self.valor_total:
            raise ValidationError('O valor informado é maior do que o valor restante de pagamento')

        return self.valor_total - self.valor_pago

    @property
    def status_pagamento(self):
        if self.valor_pago == 0:
            return 'AGUARDANDO'
        elif self.valor_pago < self.valor_total:
            return 'PARCIAL'
        else:
            return 'PAGO'

    def verificar_e_creditar_pontos(self):
        if(
            self.valor_pago >= self.valor_total and
            not self.pontos_creditados
        ):
            pontos = int(self.valor_total/VALOR_POR_PONTO)

            if pontos > 0:
                cliente = self.cliente
                self.cliente.pontos += pontos

                while cliente.pontos >= PONTOS_POR_CUPOM:
                    cliente.pontos -= PONTOS_POR_CUPOM
                    cliente.cupons += 1

                self.cliente.save()

            self.pontos_creditados = True
            self.save()

    def atualizar_data_limite(self):
        if self.valor_pago == 0:
            self.data_limite_pagamento = date.today() + timedelta(days=1)
        elif self.valor_pago < self.valor_total:
            self.data_limite_pagamento = date.today() + timedelta(days=5)
        else:
            self.data_limite_pagamento = None

        self.save(update_fields=['data_limite_pagamento'])
    def __str__(self):
        return f'Pedido:{self.cliente}'

    @property
    def proximo_status_permitido(self):
        fluxo={
            'PENDENTE': ['PEDIDO'],
            'PEDIDO': ['CHEGOU'],
            'CHEGOU': ['ENVIADO'],
            'ENVIADO': ['ENTREGUE'],
            'ENTREGUE': [],
        }
        return fluxo.get(self.status_encomenda,[])
    def pode_mudar_para(self,novo_status):
        #FLUXO BASE
        fluxo = self.proximo_status_permitido

        #REGRA DE FLUXO
        if novo_status not in fluxo:
            return False, "Transição inválida de status"

        #REGRA DE PAGAMENTO
        if self.valor_pago < self.valor_total:
            if novo_status in ['ENVIADO','ENTREGUE']:
                return False,"Pagamento ainda não foi concluido"

        return True, ""

#===================== ITEM PEDIDO =========================

class ItemPedido(models.Model):
    TIPO_VENDA=[
        ('ESTOQUE','Estoque'),
        ('ENCOMENDA','Encomenda') ,
    ]

    pedido = models.ForeignKey(Pedido,on_delete=models.CASCADE,related_name='itens')
    produto = models.ForeignKey(Produto,on_delete=models.SET_NULL,null=True,blank=True,related_name='itens_pedido')
    nome_produto = models.CharField(max_length=100, null=True,blank=True)
    tipo = models.CharField(max_length=15,choices=TIPO_VENDA)
    quantidade = models.IntegerField(default=0)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2,default=0)



    def valor_total_item(self):
        return self.valor_unitario * self.quantidade

    def clean(self):
        # DEVE TER PRODUTO OU NOME_PRODUTO
        if not self.produto and not self.nome_produto:
            raise ValidationError('Informe um produto ou nome do produto')

        # QUANTIDADE OBRIGATÓRIA
        if not self.quantidade or self.quantidade <= 0:
            raise ValidationError('Quantidade deve ser maior que zero')

        # ESTOQUE → precisa de produto
        if self.tipo == 'ESTOQUE' and not self.produto:
            raise ValidationError('Selecione um produto para itens de estoque')

        # ENCOMENDA → regras novas
        if self.tipo == 'ENCOMENDA':
            # Precisa inserir o valor do produto
            if self.valor_unitario is None or self.valor_unitario <= 0:
                raise ValidationError('Informe um valor válido')

            # se NÃO tem produto → precisa nome
            if not self.produto and not self.nome_produto:
                raise ValidationError('Informe o nome do produto para encomenda')

            # se NÃO tem produto → precisa valor
            if not self.produto and not self.valor_unitario:
                raise ValidationError('Informe o valor do produto encomendado')

    def save(self,*args,**kwargs):
        item_antigo = None
        is_new = self.pk is None

        if not is_new:
            try:
                item_antigo = ItemPedido.objects.get(pk=self.pk)
            except ItemPedido.DoesNotExist:
                pass
        #VALIDA ESTOQUE ANTES
        if is_new and self.tipo == 'ESTOQUE' and self.produto and self.quantidade:
            if self.quantidade > self.produto.estoque_disponivel:
                raise ValidationError({'quantidade':'Estoque insuficiente'})
        #GARANTE VALOR UNITÁRIO
        if self.produto and (not self.valor_unitario or self.valor_unitario == 0):
            self.valor_unitario = self.produto.preco_unitario
        #VALIDA MODEL
        self.full_clean()
        #SALVA PRIMEIRO
        super().save(*args,**kwargs)
        #BAIXAR ESTOQUE (apenas na criação)
        if is_new and self.tipo == 'ESTOQUE' and self.produto and self.quantidade:
           baixar_estoque(self.produto,self.quantidade,self)

    def __str__(self):
        if self.produto:
            return f'{self.produto.nome_produto} - {self.quantidade}'
        return f'{self.nome_produto} ({self.quantidade}x)'

#===================== ITEM PEDIDO LOTE  =========================

class ItemPedidoLote(models.Model):
    item_pedido = models.ForeignKey('ItemPedido', on_delete=models.CASCADE, related_name='lotes')
    lote = models.ForeignKey('LoteProduto', on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField()
