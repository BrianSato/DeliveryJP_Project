from django.core.exceptions import ValidationError
from django.test import TestCase
from datetime import date, timedelta

from loja.models import Produto, LoteProduto, ItemPedido, Pedido, Cliente, ItemPedidoLote
from loja.utils import baixar_estoque, devolver_estoque, devolver_parcial_estoque


class EstoqueTestCase(TestCase):
    #TESTE DE STATUS DE VALIDADE
    def test_estoque_disponivel_ignora_vencidos(self):
        produto = Produto.objects.create(
            nome_produto="Produto Teste",
            preco_unitario=10
        )

        hoje = date.today()

        # Lote válido
        LoteProduto.objects.create(
            produto=produto,
            quantidade=10,
            data_validade=hoje + timedelta(days=10),
            ativo=True
        )

        # Lote vencido (não deve contar)
        LoteProduto.objects.create(
            produto=produto,
            quantidade=5,
            data_validade=hoje - timedelta(days=1),
            ativo=True
        )

        # Lote sem validade (deve contar)
        LoteProduto.objects.create(
            produto=produto,
            quantidade=3,
            data_validade=None,
            ativo=True
        )

        self.assertEqual(produto.estoque_disponivel, 13)

    def test_nao_permitir_estoque_negativo(self):
        cliente = Cliente.objects.create(nome="Cliente Teste")

        produto = Produto.objects.create(
            nome_produto="Produto Teste",
            preco_unitario=10
        )

        lote = LoteProduto.objects.create(
            produto=produto,
            quantidade=5
        )

        pedido = Pedido.objects.create(cliente=cliente)

        with self.assertRaises(ValidationError):
            ItemPedido.objects.create(
                pedido=pedido,
                produto=produto,
                quantidade=10,
                tipo="ESTOQUE"
            )

    #TESTE PRODUTO SEM LOTES
    def test_estoque_sem_lotes(self):
        produto = Produto.objects.create(
            nome_produto="Produto Vazio",
            preco_unitario=10
        )

        self.assertEqual(produto.estoque_disponivel, 0)

    #TESTE INATIVO NÃO CONTA
    def test_estoque_ignora_lote_inativo(self):
        produto = Produto.objects.create(
            nome_produto="Produto Teste",
            preco_unitario=10
        )

        LoteProduto.objects.create(
            produto=produto,
            quantidade=10,
            data_validade=None,
            ativo=False
        )

        self.assertEqual(produto.estoque_disponivel, 0)

    #TESTE DA FIFO DE ESTOQUE
class EstoqueFIFOTestCase(TestCase):

    def test_baixar_estoque_fifo_real(self):
        cliente = Cliente.objects.create(
            nome="Cliente Teste"
        )

        produto = Produto.objects.create(
            nome_produto="Produto FIFO",
            preco_unitario=10
        )

        pedido = Pedido.objects.create(
            cliente=cliente
        )

        hoje = date.today()

        lote_antigo = LoteProduto.objects.create(
            produto=produto,
            quantidade=10,
            data_validade=hoje + timedelta(days=1),
            ativo=True
        )

        lote_novo = LoteProduto.objects.create(
            produto=produto,
            quantidade=10,
            data_validade=hoje + timedelta(days=10),
            ativo=True
        )

        item_pedido = ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade=5,
            tipo="ESTOQUE"
        )

        baixar_estoque(produto, 5, item_pedido)

        lote_antigo.refresh_from_db()
        lote_novo.refresh_from_db()

        self.assertEqual(lote_antigo.quantidade, 5)
        self.assertEqual(lote_novo.quantidade, 10)



class DevolucaoEstoqueTestCase(TestCase):

    def test_devolver_estoque_retorna_fifo_corretamente(self):
        cliente = Cliente.objects.create(nome="Cliente Teste")

        produto = Produto.objects.create(
            nome_produto="Produto Teste",
            preco_unitario=10
        )

        hoje = date.today()

        lote1 = LoteProduto.objects.create(
            produto=produto,
            quantidade=10,
            data_validade=hoje + timedelta(days=1),
            ativo=True
        )

        lote2 = LoteProduto.objects.create(
            produto=produto,
            quantidade=10,
            data_validade=hoje + timedelta(days=10),
            ativo=True
        )

        pedido = Pedido.objects.create(cliente=cliente)

        item = ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade=5,
            tipo="ESTOQUE"
        )

        baixar_estoque(produto, 5, item)

        devolver_estoque(item)

        lote1.refresh_from_db()
        lote2.refresh_from_db()

        self.assertEqual(lote1.quantidade, 10)
        self.assertEqual(lote2.quantidade, 10)

    def test_devolver_estoque_restaurar_quantidade(self):
        # Criar cliente
        cliente = Cliente.objects.create(nome="Cliente Teste")

        # Criar produto
        produto = Produto.objects.create(
            nome_produto="Produto Teste",
            preco_unitario=10
        )

        # Criar lote
        lote = LoteProduto.objects.create(
            produto=produto,
            quantidade=10,
            data_validade=date.today() + timedelta(days=10)
        )

        # Criar pedido
        pedido = Pedido.objects.create(cliente=cliente)

        # Criar item (vai baixar estoque automaticamente)
        item = ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade=4,
            valor_unitario=10,
            tipo='ESTOQUE'
        )

        baixar_estoque(produto, 4, item)

        # Atualiza lote
        lote.refresh_from_db()
        self.assertEqual(lote.quantidade, 6)

        # Devolver estoque
        devolver_estoque(item)

        lote.refresh_from_db()
        self.assertEqual(lote.quantidade, 10)

    def test_nao_devolver_duas_vezes(self):
        cliente = Cliente.objects.create(nome="Cliente Teste")

        produto = Produto.objects.create(
            nome_produto="Produto Teste",
            preco_unitario=10
        )

        lote = LoteProduto.objects.create(
            produto=produto,
            quantidade=10,
            data_validade=date.today() + timedelta(days=10)
        )

        pedido = Pedido.objects.create(cliente=cliente)

        item = ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade=4,
            valor_unitario=10,
            tipo='ESTOQUE'
        )

        baixar_estoque(produto, 4, item)

        devolver_estoque(item)
        devolver_estoque(item)  # tenta devolver de novo

        lote.refresh_from_db()
        self.assertEqual(lote.quantidade, 10)  # não pode passar disso

    def test_devolver_parcial_estoque(self):
        cliente = Cliente.objects.create(nome="Cliente Teste")

        produto = Produto.objects.create(
            nome_produto="Produto Teste",
            preco_unitario=10
        )

        hoje = date.today()

        lote = LoteProduto.objects.create(
            produto=produto,
            quantidade=10,
            data_validade=hoje + timedelta(days=10)
        )

        pedido = Pedido.objects.create(cliente=cliente)

        item = ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade=6,
            tipo="ESTOQUE"
        )

        baixar_estoque(produto, 6, item)

        lote.refresh_from_db()
        self.assertEqual(lote.quantidade, 4)

        # devolve só parte
        devolver_parcial_estoque(item, 2)

        lote.refresh_from_db()
        self.assertEqual(lote.quantidade, 6)

