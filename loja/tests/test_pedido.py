from django.test import TestCase
from loja.models import Pedido, LoteProduto, Produto, Cliente, ItemPedido
from loja.utils import processar_expiracao_pedido, baixar_estoque

from django.utils import timezone
from datetime import timedelta

class PedidoTestCase(TestCase):

    def test_expiracao_pedido_devolve_estoque(self):

        cliente = Cliente.objects.create(nome="Cliente Teste")

        produto = Produto.objects.create(
            nome_produto="Produto Teste",
            preco_unitario=10
        )

        lote = LoteProduto.objects.create(
            produto=produto,
            quantidade=10,
            data_validade=timezone.now().date() + timedelta(days=10)
        )

        # 🔥 pedido já vencido
        pedido = Pedido.objects.create(
            cliente=cliente,
            data_pedido=timezone.now() - timedelta(days=5),
            data_limite_pagamento=timezone.now() - timedelta(days=1)
        )

        item = ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade=4,
            tipo="ESTOQUE"
        )

        baixar_estoque(produto, 4, item)

        lote.refresh_from_db()
        self.assertEqual(lote.quantidade, 6)

        # 🔥 executa expiração
        processar_expiracao_pedido(pedido)

        pedido.refresh_from_db()
        lote.refresh_from_db()

        # 🔥 valida tudo
        self.assertEqual(pedido.status, "EXPIRADO")
        self.assertEqual(lote.quantidade, 10)

    def test_pedido_pago_nao_expira(self):

        cliente = Cliente.objects.create(nome="Cliente Teste")

        produto = Produto.objects.create(
            nome_produto="Produto Teste",
            preco_unitario=10
        )

        # criar estoque
        lote = LoteProduto.objects.create(
            produto=produto,
            quantidade=10,
            data_validade=timezone.now().date() + timedelta(days=10)
        )

        pedido = Pedido.objects.create(
            cliente=cliente,
            data_limite_pagamento=timezone.now() - timedelta(days=1)
        )

        item = ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade=2,
            valor_unitario=10,
            tipo="ESTOQUE"
        )

        # baixa estoque manual
        baixar_estoque(produto, 2, item)

        # simula pagamento
        pedido.valor_pago = 20
        pedido.save()

        self.assertEqual(pedido.status_pagamento, 'PAGO')

        processar_expiracao_pedido(pedido)

        pedido.refresh_from_db()

        # não deve expirar
        self.assertNotEqual(pedido.status, 'EXPIRADO')

    def test_expiracao_nao_devolve_duas_vezes(self):

        cliente = Cliente.objects.create(nome="Cliente Teste")

        produto = Produto.objects.create(
            nome_produto="Produto Teste",
            preco_unitario=10
        )

        lote = LoteProduto.objects.create(
            produto=produto,
            quantidade=10,
            data_validade=timezone.now().date() + timedelta(days=10)
        )

        pedido = Pedido.objects.create(
            cliente=cliente,
            data_limite_pagamento=timezone.now() - timedelta(days=1)
        )

        item = ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade=4,
            tipo="ESTOQUE"
        )

        baixar_estoque(produto, 4, item)

        processar_expiracao_pedido(pedido)
        processar_expiracao_pedido(pedido)  # chama de novo

        lote.refresh_from_db()

        self.assertEqual(lote.quantidade, 10)