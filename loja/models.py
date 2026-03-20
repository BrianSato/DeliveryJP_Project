from django.core.exceptions import ValidationError
from django.db import models
from datetime import date, timedelta


class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20, unique=True)
    endereco = models.CharField(max_length=200)
    pontos = models.IntegerField(default=0)
    validade_pontos = models.DateField(blank=True,null=True)
    data_cadastro = models.DateField(auto_now_add=True)

    @property
    def saldo_devedor(self):
        vendas = Venda.objects.filter(
            cliente=self,
            status__in=['PENDENTE','PARCIAL']
        )
        total = sum(v.valor_total - v.valor_pago for v in vendas)

        return total

    def __str__(self):
        return self.nome

class Produto(models.Model):
    nome_produto = models.CharField(max_length=100)
    preco_unitario = models.DecimalField(max_digits=10,decimal_places=2)
    ativo = models.BooleanField(default=True)

    @property
    def estoque_total(self):
        return sum(lote.quantidade for lote in self.loteproduto_set.all())

    def total_encomendados(self):
        return self.encomenda_set.filter(
            status__in=['PEDIDO','ENVIADO','CHEGOU','ENTREGUE']
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

    def __str__(self):
        return self.nome_produto

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

    def __str__(self):
        return f'{self.produto} - {self.quantidade} unidades - Validade: {self.data_validade}'

class Encomenda(models.Model):
    STATUS_PAGAMENTO =[
        ('AGUARDANDO','Aguardando pagamento inicial'),
        ('PARCIAL', 'Pagamento parcial feito'),
        ('PAGO', '100% pago'),
    ]
    STATUS_ENCOMENDA = [
        ('PENDENTE','Aguardando Pedido'),
        ('PEDIDO','Pedido feito'),
        ('CHEGOU', 'Produto chegou'),
        ('ENVIADO','Enviado'),
        ('ENTREGUE', 'Entregue ao cliente'),
        ('CANCELADO','Cancelado')
    ]
    cliente = models.ForeignKey(Cliente,on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto,on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField()
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status_pagamento = models.CharField(max_length=20,choices=STATUS_PAGAMENTO,default='AGUARDANDO')
    status = models.CharField(max_length=20,choices=STATUS_ENCOMENDA,default='PENDENTE')

    data_encomenda = models.DateField(auto_now_add=True)
    data_limite_pagamento = models.DateField(null=True, blank=True)

    def clean(self):
        valor_total = self.valor_total or (self.produto.preco_unitario * self.quantidade)
        valor_pago = self. valor_pago or 0

        #Vvalor pago não pode ser maior que o total
        if valor_pago > valor_total:
            raise ValidationError('O valor pago não pode ser maior que o total')
        #não pode fazer pedido sem pagamento
        if self.status != 'PENDENTE' and valor_pago == 0:
            raise ValidationError('Não é possível fazer o pedido sem pagamento')
        #não pode enviar sem pagamento total:
        if self.status == 'ENVIADO' or self.status == 'ENTREGUE' and valor_pago < valor_total:
            raise ValidationError('Só é possível enviar após pagamento total')

    def save(self,*args,**kwargs):
        self.valor_total = self.produto.preco_unitario * self.quantidade
        valor_pago = self.valor_pago or 0
        valor_total = self.valor_total or 0
        status_anterior = None
        encomenda_antiga = None

        if self.pk:
            encomenda_antiga = Encomenda.objects.get(pk=self.pk)
            status_anterior = encomenda_antiga.status_pagamento

        #atualiza status automaticamente e impôem data limite de pagamento
        #AGUARDANDO
        if valor_pago <= 0:
            self.status_pagamento = 'AGUARDANDO'
            if status_anterior != 'AGUARDANDO':
                self.data_limite_pagamento = date.today() + timedelta(days=1)
        #PARCIALMENTE PAGO
        elif valor_pago < valor_total:
            self.status_pagamento = 'PARCIAL'
            if status_anterior != 'PARCIAL':
                self.data_limite_pagamento = date.today() + timedelta(days=5)
        #TOTALMENTE PAGO
        else:
            self.status_pagamento = 'PAGO'
            self.data_limite_pagamento = None
        #CANCELAMENTO AUTOMÁTICO
        if (
            self.data_limite_pagamento and
            date.today() > self.data_limite_pagamento and
            self.status != 'CANCELADO'
        ):
            self.status = 'CANCELADO'
        #RETORNO AO ESTOQUE
        if (
            encomenda_antiga and
            encomenda_antiga.status != 'CANCELADO' and
            self.status == 'CANCELADO'
        ):
            LoteProduto.objects.create(
                produto=self.produto,
                quantidade=self.quantidade,
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.cliente} - {self.produto.nome_produto}'

class Venda(models.Model):
    TIPO_VENDA = [
        ('ESTOQUE', 'Em Estoque'),
        ('ENCOMENDA', 'Encomenda')
    ]
    STATUS = [
        ('PENDENTE', 'Pendente'),
        ('PAGO', 'Pago'),
        ('PARCIAL', 'Pago parcialmente'),
        ('CANCELADO', 'Cancelado'),
    ]
    FORMA_PAGAMENTO = [
        ('DINHEIRO', 'Dinheiro'),
        ('CARTAO', 'Cartao'),
        ('TRANSFERENCIA', 'Transferencia'),
    ]

    cliente = models.ForeignKey(Cliente,on_delete=models.CASCADE)
    data_venda = models.DateField(auto_now_add=True)
    valor_total = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    valor_pago = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    forma_pagamento = models.CharField(max_length=20, choices=FORMA_PAGAMENTO, default='DINHEIRO')
    data_limite_pagamento = models.DateField(verbose_name='Data limite de pagamento',null=False,blank=False)
    status = models.CharField(max_length=20,choices=STATUS,default='PENDENTE')
    tipo_venda = models.CharField(max_length=20,choices=TIPO_VENDA,default='ESTOQUE')

    def atualizar_valor_total(self):
        total = sum(item.subtotal for item in self.itemvenda_set.all())
        self.valor_total = total
        self.save()

    def atualizar_status_pagamento(self):
        if self.valor_pago == 0 and self.data_limite_pagamento < date.today():
            self.status = 'CANCELADO'
        elif self.valor_pago == 0:
            self.status = 'PENDENTE'
        elif self.valor_pago < self.valor_total:
            self.status = 'PARCIAL'
        elif self.valor_pago >= self.valor_total:
            self.status = 'PAGO'

    def save(self,*args,**kwargs):
        self.atualizar_status_pagamento()
        super().save(*args,**kwargs)

    def __str__(self):
        return f'{self.cliente} - {self.data_venda}'

class ItemVenda(models.Model):
    venda = models.ForeignKey(Venda,on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto,on_delete=models.CASCADE)

    quantidade = models.IntegerField()
    preco_unitario = models.DecimalField(max_digits=10,decimal_places=2)
    subtotal = models.DecimalField(max_digits=10,decimal_places=2)

    def clean(self):
        #se não houver selecionado nenhum produto
        if not self.produto:
            raise ValidationError('Selecione um produto')
        #se não houve quantidade suficiente no estoque
        if self.quantidade > self.produto.estoque_total:
            raise ValidationError(
                f'Estoque insuficiente para {self.produto.nome_produto}'
                f'Estoque disponível:{self.produto.estoque_total}'
            )

    def save(self,*args,**kwargs):
        #preencher automaticamente
        self.preco_unitario = self.produto.preco_unitario
        #calcula subtotal
        self.subtotal = self.quantidade * self.preco_unitario

        #atualiza estoque dos lotes automaticamente(FIFO)
        qnt_a_retirar = self.quantidade
        lotes = LoteProduto.objects.filter(produto=self.produto).order_by('data_validade')
        for lote in lotes:
            if qnt_a_retirar <= 0:
                break
            if lote.quantidade >= qnt_a_retirar:
                lote.quantidade -= qnt_a_retirar
                lote.save()
                qnt_a_retirar = 0
            else:
                qnt_a_retirar -= lote.quantidade
                lote.quantidade = 0
                lote.save()

        super().save(*args,**kwargs)
        #atualizad valor total da venda
        self.venda.atualizar_valor_total()
        #atualiza os status da venda baseado no pagamento
        self.venda.atualizar_status_pagamento()

    def __str__(self):
        return f'{self.produto} - {self.quantidade}'

class Pagamento(models.Model):
    venda = models.OneToOneField(Venda,on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.venda.cliente.nome} - {self.venda.status} - {self.venda.forma_pagamento}'

    @property
    def status(self):
        return self.venda.status
    @property
    def forma_pagamento(self):
        return self.venda.forma_pagamento
    @property
    def valor_total(self):
        return self.venda.valor_total
    @property
    def data_limite_pagamento(self):
        return self.venda.data_limite_pagamento


