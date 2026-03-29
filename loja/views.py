from datetime import datetime
from decimal import Decimal
from gc import get_objects

from django.db.models import Q
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from pyexpat.errors import messages

from loja.models import Cliente, Produto, LoteProduto, Pedido, ItemPedido
from loja.utils import criar_lote


#Home protegida
@login_required
def home(request):
    return render(request,'loja/home.html')

#Tela de login personalizada
class MyloginView(LoginView):
    template_name = 'loja/login.html'
    redirect_authenticated_user = True

    #Sempre redireciona para /cliente/ após login
    def get_success_url(self):
        return '/cliente/'

#Tela de Novo Cliente
@login_required
def cliente_create(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        telefone = request.POST.get('telefone')
        endereco = request.POST.get('endereco')

        #Cria e salva no banco
        Cliente.objects.create(nome=nome,telefone=telefone,endereco=endereco)

        return redirect('cliente_create')

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
@login_required
def cliente_detail(request,id):
    cliente = get_object_or_404(Cliente, id=id)

    return render(request,'loja/cliente_detail.html',{
        'cliente':cliente
    })
@login_required
def produto_menu(request):
    return render(request,'loja/produto_menu.html')

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

        return redirect('produto_list')

    return render(request,'loja/produto_create.html')

@login_required
def produto_list(request):
    produtos = Produto.objects.all()
    query = request.GET.get('q')
    if query:
        produtos = produtos.filter(
            Q(nome_produto__icontains=query)
        )
    return render(request,'loja/produto_list.html',{
        'produtos':produtos,
        'query':query,
    })

@login_required
def produto_detail(request,id):
    produto = get_object_or_404(Produto, id=id)
    if request.method == 'POST':
        quantidade = request.POST.get('quantidade')
        data_validade = request.POST.get('data_validade')

        criar_lote(produto,quantidade,data_validade)

        return redirect('produto_detail',produto_id= produto.id)

    lotes= produto.loteproduto_set.filter(quantidade__gt=0).order_by('data_validade')

    return render(request,'loja/produto_detail.html',{
        'produto':produto,
        'lotes':lotes
    })

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

@login_required
def pedido_list(request):
    pedidos = Pedido.objects.all()

    return render(request,'loja/pedido_list.html',{
        'pedidos':pedidos,
    })

@login_required
def pedido_detail(request,pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    # ATUALIZAR PAGAMENTO
    valor_pago = request.POST.get('valor_pago')
    if valor_pago:
        pedido.valor_pago += Decimal(valor_pago)
        pedido.save()

    if request.method == 'POST':
        #ATUALIZAR STATUS DO ITEM
        item_id = request.POST.get('item_id')
        novo_status = request.POST.get('status_item')

        if item_id and novo_status:
            item= ItemPedido.objects.get(id=item_id)

            #REGRA DE NEGÓCIO
            if novo_status in ['ENVIADO','ENTREGUE']:
                if pedido.valor_pago < pedido.valor_total:
                    messages.error(request, 'Só é possível enviar após pagamento total')
                    return redirect('pedido_detail',pedido_id= pedido.id)

            item.status_item = novo_status
            item.save()

        return redirect('pedido_detail',pedido_id= pedido.id)
    #CRIA NOVO PEDIDO
    if request.method == 'POST':
        quantidade = int(request.POST.get('quantidade')or 0)
        tipo= request.POST.get('tipo')
        if tipo == 'ESTOQUE':
            produto_id = request.POST.get('produto')
            produto= Produto.objects.get(id=produto_id)

            ItemPedido.objects.create(
                pedido=pedido,
                produto=produto,
                quantidade=quantidade,
                valor_unitario=produto.preco_unitario,
                tipo=tipo
           )
        else: #ENCOMENDA
            nome_produto= request.POST.get('nome_produto')
            valor_unitario= request.POST.get('valor_unitario')

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
