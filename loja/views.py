import re
from datetime import date, timedelta
from decimal import Decimal

from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Q, Sum
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages

from loja.models import Cliente, Produto, LoteProduto, Pedido, ItemPedido
from loja.utils import criar_lote

#Tela de login personalizada
class MyloginView(LoginView):
    template_name = 'loja/login.html'
    redirect_authenticated_user = True

    #Sempre redireciona para /cliente/ após login
    def get_success_url(self):
        return '/cliente/'
#Home protegida
@login_required
def home(request):
    hoje = timezone.now().date()
    limite = hoje + timedelta(days=7)
    vencidos_qtd = LoteProduto.objects.filter(data_validade__lt=hoje).count()
    vencendo_qtd = LoteProduto.objects.filter(data_validade__range=(hoje,limite)).count()

    return render(request, 'loja/home.html', {
        'vencidos_qtd': vencidos_qtd,
        'vencendo_qtd': vencendo_qtd
    })
#Tela de Produtos Vencidos
def produtos_vencidos(request):
    hoje = timezone.now().date()
    vencidos = (LoteProduto.objects
                .filter(data_validade__lt=hoje)
                .values('produto__id','produto__nome_produto')
                .annotate(total=Sum('quantidade'))
                .order_by('produto__nome_produto')
    )
    return render(request,'loja/estoque_vencidos.html',{
        'vencidos':vencidos,
    })
#Tela de Produtos Vencendo
def produtos_vencendo(request):
    hoje = timezone.now().date()
    vencendo = (LoteProduto.objects
                .filter(data_validade__range=(hoje, hoje + timedelta(days=7)))
                .values('produto__id', 'produto__nome_produto')
                .annotate(total=Sum('quantidade'))
                .order_by('produto__nome_produto')
    )

    return render(request, 'loja/estoque_vencendo.html', {
        'vencendo': vencendo,
    })

#Tela de Novo Cliente
@login_required
def cliente_create(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        endereco = request.POST.get('endereco')
        telefone = request.POST.get('telefone','')
        telefone_limpo = re.sub(r'\D','', telefone)
        if len(telefone_limpo) != 11:
            return render(request,'loja/cliente.html',{
                'erro': 'Este campo só aceita 11 NÚMEROS',
                'nome': nome,
                'telefone':telefone,
                'endereco': endereco
            })
        if Cliente.objects.filter(telefone=telefone_limpo).exists():
            return render(request,'loja/cliente.html',{
                'erro':'Este telefone já está cadastrado',
                'nome': nome,
                'telefone':telefone,
                'endereco': endereco
            })

        #Cria e salva no banco
        Cliente.objects.create(nome=nome,telefone=telefone_limpo,endereco=endereco)

        return redirect('cliente_list')

    return render(request,'loja/cliente.html')

#Tela de Lista de Clientes
@login_required
def cliente_list(request):
    query = request.GET.get('q')
    clientes = Cliente.objects.all()
    if query:
        clientes = clientes.filter(
            Q(nome__icontains=query) |
            Q(telefone__icontains=query)
        )
    return render(request,'loja/cliente_list.html',{
        'clientes':clientes,
        'query':query
    })
#Tela da lista de Cliente
@login_required
def cliente_detail(request,id):
    cliente = get_object_or_404(Cliente, id=id)
    pedidos = cliente.pedidos.all()

    return render(request,'loja/cliente_detail.html',{
        'cliente':cliente,
        'pedidos':pedidos,
    })
#Tela do Menu de Produtos
@login_required
def produto_menu(request):
    return render(request,'loja/produto_menu.html')
#Tela de Novo Produto
@login_required
def produto_create(request):
    if request.method == 'POST':
        nome = request.POST.get('nome_produto')
        preco = request.POST.get('preco_unitario')

        #Cria e salva no banco
        Produto.objects.create(
            nome_produto=nome,
            preco_unitario=preco if preco else 0
        )

        return redirect('produto_estoque_list')

    return render(request,'loja/produto_create.html')
#Tela da Lista de Produtos no Estoque
@login_required
def produto_estoque_list(request):
    produtos = Produto.objects.all()
    query = request.GET.get('q')
    if query:
        produtos = produtos.filter(
            Q(nome_produto__icontains=query)
        )
    return render(request,'loja/produto_estoque_list.html',{
        'produtos':produtos,
        'query':query,
    })
#Tela da Lista de Produtos Encomendados
@login_required
def produto_encomenda_list(request):
    itens = ItemPedido.objects.filter(tipo='ENCOMENDA')

    return render(request,'loja/produto_encomenda_list.html',{
        'itens': itens
    })
#Tela de Detalhes do Produtos
@login_required
def produto_detail(request,id):
    produto = get_object_or_404(Produto, id=id)
    hoje = timezone.now().date()
    filtro = request.GET.get('filtro','')
    lotes = produto.lotes.all()

    if filtro == 'vencidos':
        lotes = lotes.filter(data_validade__lt=hoje)
    elif filtro == 'vencendo':
        lotes = lotes.filter(data_validade__range=(hoje, hoje+timedelta(days=7)))
    else:
        lotes = lotes.filter(quantidade__gt=0)

    lotes = lotes.order_by('data_validade')

    if request.method == 'POST':
        quantidade = request.POST.get('quantidade')
        data_validade = request.POST.get('data_validade')

        criar_lote(produto,quantidade,data_validade)

        return redirect('produto_detail',produto_id= produto.id)

    return render(request,'loja/produto_detail.html',{
        'produto':produto,
        'lotes':lotes,
        'filtro':filtro
    })
#Tela de novo Lote do Produto
@login_required
def lote_create(request,produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    if request.method == 'POST':
        quantidade = request.POST.get('quantidade')
        data_validade = request.POST.get('data_validade')

        criar_lote(produto,quantidade,data_validade)

        return redirect('produto_detail',id= produto_id)

    return render(request,'loja/lote_create.html',{
        'produto': produto
    })
#Tela de Novo Pedido
@login_required
def pedido_create(request):
    if request.method == 'POST':
        cliente_id=request.POST.get('cliente')
        cliente= Cliente.objects.get(id=cliente_id)
        pedido = Pedido.objects.create(cliente=cliente)

        return redirect('pedido_detail', pedido_id= pedido.id)

    clientes = Cliente.objects.all()

    return render(request,'loja/pedido_create.html',{
        'clientes':clientes
    })
#Tela de Lista de Pedidos
@login_required
def pedido_list(request):
    pedidos = Pedido.objects.all()
    query = request.GET.get('q')
    if query:
        pedidos = pedidos.filter(
            Q(cliente__nome__icontains = query) |
            Q(cliente__telefone__icontains = query)
        )
    return render(request,'loja/pedido_list.html',{
        'pedidos':pedidos,
        'query':query
    })
#Tela de Detalhes do Pedido
@login_required
def pedido_detail(request,pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        # CRIA NOVO ITEM
        if action == 'adicionar_item':
            # BLOQUEIA CRIAÇÃO DE PEDIDO JÁ FEITO
            if pedido.status == 'FECHADO':
                messages.error(request, 'Pedido já finalizado')
                return redirect('pedido_detail', pedido_id=pedido.id)

            quantidade = int(request.POST.get('quantidade') or 0)
            tipo = request.POST.get('tipo')

            if tipo == 'ESTOQUE':
                produto_id = request.POST.get('produto')
                if produto_id:
                    produto = Produto.objects.get(id=produto_id)

                    ItemPedido.objects.create(
                        pedido=pedido,
                        produto=produto,
                        quantidade=quantidade,
                        valor_unitario=produto.preco_unitario,
                        tipo=tipo
                    )
            elif tipo == 'ENCOMENDA':  # ENCOMENDA
                nome_produto = request.POST.get('nome_produto')
                valor_unitario = request.POST.get('valor_unitario')
                if nome_produto and valor_unitario:
                    ItemPedido.objects.create(
                        pedido=pedido,
                        nome_produto=nome_produto,
                        quantidade=quantidade,
                        valor_unitario=valor_unitario,
                        tipo=tipo
                    )

            return redirect('pedido_detail', pedido_id=pedido.id)
        # PAGAMENTOS
        if action == 'atualizar_pagamento':
            valor_pago = request.POST.get('valor_pago')
            # ATUALIZAR PAGAMENTO
            if valor_pago:
                pedido.valor_pago += Decimal(valor_pago)
                pedido.save()
                pedido.verificar_e_creditar_pontos()
                return redirect('pedido_detail', pedido_id=pedido.id)
        if action == 'forma_pagamento':
            forma_pagamento = request.POST.get('forma_pagamento')
            # FORMA DE PAGAMENTO
            if forma_pagamento:
                pedido.forma_pagamento = forma_pagamento
                pedido.save()
                return redirect('pedido_detail', pedido_id=pedido.id)
        if action == 'usar_cupom':
            if pedido.status == 'FECHADO':
                messages.error(request,'Pedido já finalizado')
                return redirect('pedido_detail', pedido_id=pedido.id)

            cliente = pedido.cliente

            if cliente.cupons > 0 and not pedido.cupom_usado:
                cliente.cupons -= 1
                cliente.save()

                pedido.desconto = 1000
                pedido.cupom_usado = True
                pedido.save()
        #FINALIZAR PEDIDO E MUDA STATUS PARA FECHADO
        if action == 'finalizar':
            if pedido.status != 'FECHADO':
                pedido.status = 'FECHADO'
                pedido.save()
            return redirect('pedido_detail', pedido_id=pedido.id)

    if request.method == 'POST':
        valor_pago = request.POST.get('valor_pago')
        forma_pagamento = request.POST.get('forma_pagamento')
        # ATUALIZAR PAGAMENTO
        if valor_pago:
            pedido.valor_pago += Decimal(valor_pago)
        # FORMA DE PAGAMENTO
        if forma_pagamento:
            pedido.forma_pagamento = forma_pagamento
        pedido.save()

        #CRIA NOVO ITEM
        quantidade = int(request.POST.get('quantidade')or 0)
        tipo= request.POST.get('tipo')

        if tipo == 'ESTOQUE':
            produto_id = request.POST.get('produto')
            if produto_id:
                produto = Produto.objects.get(id=produto_id)

                ItemPedido.objects.create(
                    pedido=pedido,
                    produto=produto,
                    quantidade=quantidade,
                    valor_unitario=produto.preco_unitario,
                    tipo=tipo
               )
        elif tipo == 'ENCOMENDA': #ENCOMENDA
            nome_produto= request.POST.get('nome_produto')
            valor_unitario= request.POST.get('valor_unitario')
            if nome_produto and valor_unitario:

                ItemPedido.objects.create(
                    pedido=pedido,
                    nome_produto=nome_produto,
                    quantidade=quantidade,
                    valor_unitario=valor_unitario,
                    tipo=tipo
                )

        return redirect('pedido_detail',pedido_id= pedido.id)

    produtos= Produto.objects.all()
    return render(request,'loja/pedido_detail.html',{
        'pedido':pedido,
        'produtos':produtos
    })
@login_required
def pedido_encomenda_detail(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    itens = pedido.itens.filter(tipo='ENCOMENDA')

    if request.method == "POST":
        novo_status = request.POST.get("status_encomenda")

        if novo_status:
            #  REGRA DE NEGÓCIO
            if not pedido.pode_mudar_para(novo_status):
                messages.error(request,"Transição inválida ou pagamento pendente")
                return redirect('pedido_encomenda_detail', pedido_id=pedido_id)

            pedido.status_encomenda = novo_status
            pedido.save()

            messages.success(request, "Status atualizado!")

        return redirect('pedido_encomenda_detail', pedido_id=pedido.id)

    return render(request, 'loja/pedido_encomenda_detail.html', {
        'pedido': pedido,
        'itens': itens
    })