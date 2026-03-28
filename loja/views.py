from gc import get_objects

from django.db.models import Q
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from loja.models import Cliente, Produto, LoteProduto
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
