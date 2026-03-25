from gc import get_objects

from django.db.models import Q
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from loja.models import Cliente, Produto


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

#Tela Cliente Menu
@login_required
def cliente_menu(request):
    return render(request,'loja/cliente_menu.html')

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
    return render(request,'loja/produto_list.html',{
        'produtos':produtos
    })

@login_required
def produto_detail(request):
    produto = get_object_or_404(Produto, id=id)
    lotes= produto.loteproduto_set.all()
    return render(request,'loja/produto_detail.html',{
        'produtos':produto,
        'lotes:':lotes
    })
