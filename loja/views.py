import re
from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q, Sum, OuterRef, Exists
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages

from loja.forms import ClienteForm, ProdutoEstoqueForm
from loja.models import Cliente, Produto, LoteProduto, Pedido, ItemPedido
from loja.utils import criar_lote, devolver_estoque, devolver_parcial_estoque, baixar_estoque, \
    processar_expiracao_pedido


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
    vencidos_qtd = LoteProduto.objects.filter(quantidade__gt=0,data_validade__lt=hoje).count()
    vencendo_qtd = LoteProduto.objects.filter( data_validade__range=(hoje,limite)).count()

    return render(request, 'loja/home.html', {
        'vencidos_qtd': vencidos_qtd,
        'vencendo_qtd': vencendo_qtd
    })
#Tela de Produtos Vencidos
def produtos_vencidos(request):
    hoje = timezone.now().date()
    vencidos = (LoteProduto.objects
                .filter(quantidade__gt=0,data_validade__lt=hoje)
                .values('produto__id','produto__nome_produto')
                .annotate(total=Sum('quantidade'))
                .filter(total__gt=0)
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
            return render(request,'loja/cliente_create.html',{
                'erro': 'Este campo só aceita 11 NÚMEROS',
                'nome': nome,
                'telefone':telefone,
                'endereco': endereco
            })
        if Cliente.objects.filter(telefone=telefone_limpo).exists():
            return render(request,'loja/cliente_create.html',{
                'erro':'Este telefone já está cadastrado',
                'nome': nome,
                'telefone':telefone,
                'endereco': endereco
            })

        #Cria e salva no banco
        Cliente.objects.create(nome=nome,telefone=telefone_limpo,endereco=endereco)

        return redirect('cliente_list')

    return render(request,'loja/cliente_create.html')
#Editar Cliente
def cliente_update(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)

        if form.is_valid():
            form.save()
            messages.success(request, "Cliente atualizado com sucesso!")
            return redirect('cliente_list')  # ou cliente_detail

    else:
        form = ClienteForm(instance=cliente)

    return render(request, 'loja/cliente_update.html', {
        'form': form,
        'cliente': cliente
    })
#Lista de Clientes
@login_required
def cliente_list(request):
    query = request.GET.get('q')
    mostrar_inativos = request.GET.get('inativos')

    # lógica principal
    if mostrar_inativos:
        clientes_list = Cliente.objects.filter(ativo=False).order_by('-id')
    else:
        clientes_list = Cliente.objects.filter(ativo=True).order_by('-id')

    # filtro de busca
    if query:
        clientes_list = clientes_list.filter(
            Q(nome__icontains=query) |
            Q(telefone__icontains=query)
        )

    paginator = Paginator(clientes_list, 5)
    page_number = request.GET.get('page')
    clientes = paginator.get_page(page_number)

    return render(request, 'loja/cliente_list.html', {
        'clientes': clientes,
        'query': query,
        'mostrar_inativos': mostrar_inativos
    })
#Detalhes de Cliente
@login_required
def cliente_detail(request,id):
    cliente = get_object_or_404(Cliente, id=id)
    pedidos = cliente.pedidos.all()

    return render(request,'loja/cliente_detail.html',{
        'cliente':cliente,
        'pedidos':pedidos,
    })
# Apagar/Desativar Cliente
def cliente_delete(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == 'POST':
        cliente.ativo = False
        cliente.save()
        messages.success(request, 'Cliente desativado com sucesso.')
        return redirect('cliente_list')

    return redirect('cliente_detail', cliente_id=cliente.id)
# Reativar Cliente
def cliente_reativar(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == 'POST':
        cliente.ativo = True
        cliente.save()
        messages.success(request, 'Cliente reativado com sucesso.')

    return redirect('cliente_list')
#Menu de Produtos
@login_required
def produto_menu(request):
    return render(request,'loja/produto_menu.html')
#Novo Produto
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
#Produto Estoque Editar
@login_required
def produto_estoque_update(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)

    if request.method == 'POST':
        form = ProdutoEstoqueForm(request.POST, instance=produto)

        if form.is_valid():
            form.save()
            messages.success(request, 'Produto atualizado com sucesso.')
            return redirect('produto_estoque_list')
    else:
        form = ProdutoEstoqueForm(instance=produto)

    return render(request, 'loja/produto_estoque_form.html', {
        'form': form,
        'produto': produto
    })
#Produto Estoque  Apagar/Desativar
@login_required
def produto_estoque_delete(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)

    if request.method == 'POST':
        produto.ativo = False
        produto.save()
        messages.success(request, 'Produto desativado com sucesso.')

    return redirect('produto_estoque_list')
#Produto Estoque Reativar
@login_required
def produto_estoque_reativar(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)

    if request.method == 'POST':
        produto.ativo = True
        produto.save()
        messages.success(request, 'Produto reativado com sucesso.')

    return redirect('produto_estoque_list')
#Lista de Produtos no Estoque
@login_required
def produto_estoque_list(request):
    hoje = timezone.now().date()
    produtos_list = Produto.objects.all().order_by('-id')
    query = request.GET.get('q')
    filtro = request.GET.get('filtro', '')

    # 🔍 BUSCA
    if query:
        produtos_list = produtos_list.filter(
            Q(nome_produto__icontains=query)
        )

    # 🔥 SUBQUERY PARA VENCIDOS
    lotes_vencidos = LoteProduto.objects.filter(
        produto=OuterRef('pk'),
        data_validade__lt=hoje
    )

    produtos_list = produtos_list.annotate(
        tem_vencido=Exists(lotes_vencidos)
    )

    # 🔥 FILTROS
    if filtro == 'validos':
        produtos_list = produtos_list.filter(tem_vencido=False)

    elif filtro == 'vencidos':
        produtos_list = produtos_list.filter(tem_vencido=True)

    # 📄 PAGINAÇÃO
    paginator = Paginator(produtos_list, 5)
    page_number = request.GET.get('page')
    produtos = paginator.get_page(page_number)

    return render(request, 'loja/produto_estoque_list.html', {
        'produtos': produtos,
        'query': query,
        'filtro': filtro,
    })
#Lista de Produtos Encomendados
@login_required
def produto_encomenda_list(request):
    query = request.GET.get('q')

    # 🔥 UPDATE STATUS
    if request.method == 'POST':
        pedido_id = request.POST.get('pedido_id')
        novo_status = request.POST.get('status_encomenda')

        if pedido_id and novo_status:
            pedido = Pedido.objects.get(id=pedido_id)

            if novo_status == 'ENTREGUE' and pedido.status_pagamento != 'PAGO':
                messages.error(request, 'Não é possível marcar como ENTREGUE sem pagamento completo.')
                return redirect('produto_encomenda_list')

            pedido.status_encomenda = novo_status
            pedido.save()

            messages.success(request, 'Status atualizado com sucesso.')
            return redirect('produto_encomenda_list')

    # 🔥 BASE CORRETA (ItemPedido)
    itens_list = ItemPedido.objects.filter(tipo='ENCOMENDA').order_by('-id')

    # 🔍 FILTRO PELO NOME DO CLIENTE
    if query:
        if query:
            itens_list = itens_list.filter(
                Q(nome_produto__icontains=query)
            )

    paginator = Paginator(itens_list, 5)
    page_number = request.GET.get('page')
    itens = paginator.get_page(page_number)

    return render(request, 'loja/produto_encomenda_list.html', {
        'itens': itens,
        'query': query
    })
#Detalhes do Produtos
@login_required
def produto_detail(request, id):
    produto = get_object_or_404(Produto, id=id)
    hoje = timezone.now().date()
    filtro = request.GET.get('filtro', '')

    lotes = produto.lotes.all()

    # FILTROS
    if filtro == 'vencidos':
        lotes = lotes.filter(
            data_validade__lt=hoje,
            quantidade__gt=0
        )

    elif filtro == 'vencendo':
        lotes = lotes.filter(
            data_validade__range=(hoje, hoje + timedelta(days=7)),
            quantidade__gt=0,
            ativo=True
        )

    else:
        lotes = lotes.filter(
            quantidade__gt=0,
            ativo=True
        ).filter(
            Q(data_validade__gte=hoje) | Q(data_validade__isnull=True)
        )

    lotes = lotes.order_by('data_validade')

    # CRIAÇÃO DE LOTE
    if request.method == 'POST':
        quantidade = request.POST.get('quantidade')
        data_validade = request.POST.get('data_validade')

        if quantidade:
            criar_lote(produto, quantidade, data_validade)

        return redirect('produto_detail', id=produto.id)

    return render(request, 'loja/produto_detail.html', {
        'produto': produto,
        'lotes': lotes,
        'filtro': filtro
    })
#Novo Lote do Produto
@login_required
def lote_create(request,produto_id):
    produto = get_object_or_404(Produto, id=produto_id)

    if request.method == 'POST':
        quantidade = request.POST.get('quantidade')
        data_validade = request.POST.get('data_validade')

        if quantidade:
            criar_lote(produto,quantidade,data_validade)

        return redirect('produto_detail',id= produto_id)

    return render(request,'loja/lote_create.html',{
        'produto': produto
    })
def lote_desativar(request, pk):
    lote = get_object_or_404(LoteProduto, id=pk)

    lote.ativo = False
    lote.save()

    return redirect('produto_detail', id=lote.produto.id)
#Novo Pedido
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
#Lista de Pedidos
@login_required
def pedido_list(request):
    pedidos_lista = Pedido.objects.all().order_by('-id')
    query = request.GET.get('q')
    if query:
        pedidos_lista = pedidos_lista.filter(
            Q(cliente__nome__icontains=query) |
            Q(cliente__telefone__icontains=query)
        )
    paginator = Paginator(pedidos_lista, 5)
    page_number = request.GET.get('page')
    pedidos = paginator.get_page(page_number)

    return render(request,'loja/pedido_list.html',{
        'pedidos':pedidos,
        'query':query
    })
#Detalhes do Pedido
@login_required
def pedido_detail(request,pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    processar_expiracao_pedido(pedido)
    editar_item_id = request.GET.get('editar_item')

    if request.method == 'POST':
        action = request.POST.get('action')
        # CRIA NOVO ITEM
        if action == 'adicionar_item':

            if pedido.status == 'FECHADO':
                messages.error(request, 'Pedido já finalizado')
                return redirect('pedido_detail', pedido_id=pedido.id)

            quantidade = int(request.POST.get('quantidade') or 0)
            tipo = request.POST.get('tipo')

            try:
                if tipo == 'ESTOQUE':
                    produto_id = request.POST.get('produto')
                    produto = Produto.objects.get(id=produto_id)

                    item = ItemPedido(
                        pedido=pedido,
                        produto=produto,
                        quantidade=quantidade,
                        valor_unitario=produto.preco_unitario,
                        tipo=tipo
                    )

                elif tipo == 'ENCOMENDA':
                    item = ItemPedido(
                        pedido=pedido,
                        nome_produto=request.POST.get('nome_produto'),
                        quantidade=quantidade,
                        valor_unitario=request.POST.get('valor_unitario'),
                        tipo=tipo
                    )

                else:
                    messages.error(request, "Tipo inválido")
                    return redirect('pedido_detail', pedido_id=pedido.id)

                item.full_clean()
                item.save()

                # REGRA DE NEGÓCIO CENTRALIZADA AQUI
                if tipo == 'ESTOQUE':
                    baixar_estoque(produto, quantidade, item)

            except (Produto.DoesNotExist, ValidationError) as e:
                messages.error(request, f"Erro ao adicionar item: {e}")
                return redirect('pedido_detail', pedido_id=pedido.id)

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

            if forma_pagamento:
                try:
                    pedido.forma_pagamento = forma_pagamento
                    pedido.save()
                except ValidationError as e:
                    messages.error(request, "Erro: " + ', '.join(e.messages))

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
                try:
                    pedido.status = 'FECHADO'
                    print("ITENS:", pedido.itens.count())
                    print("FORMA PAGAMENTO:", pedido.forma_pagamento)
                    pedido.save()  # AQUI CHAMA O CLEAN() DO MODEL

                except ValidationError as e:
                    print('ERRO AO FINALIZAR:',e.messages)
                    messages.error(request, ', '.join(e.messages))
                    return redirect('pedido_detail', pedido_id=pedido.id)

            return redirect('pedido_detail', pedido_id=pedido.id)

    produtos = Produto.objects.all()

    return render(request, 'loja/pedido_detail.html', {
        'pedido': pedido,
        'produtos': produtos,
        'editar_item_id': editar_item_id,
    })
@login_required
def pedido_encomenda_detail(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    itens = pedido.itens.filter(tipo='ENCOMENDA')

    if request.method == "POST":
        novo_status = request.POST.get("status_encomenda")

        if novo_status:
            permitido, mensagem = pedido.pode_mudar_para(novo_status)

            #  REGRA DE NEGÓCIO
            if not permitido:
                messages.error(request,mensagem)
                return redirect('pedido_encomenda_detail', pedido_id=pedido_id)

            pedido.status_encomenda = novo_status
            pedido.save()

            messages.success(request, "Status atualizado!")

        return redirect('pedido_encomenda_detail', pedido_id=pedido.id)

    return render(request, 'loja/pedido_encomenda_detail.html', {
        'pedido': pedido,
        'itens': itens
    })

@login_required
def itempedido_editar(request, id):
    item = get_object_or_404(ItemPedido, id=id)
    pedido = item.pedido

    if pedido.status != 'ABERTO':
        messages.error(request, "Pedido não pode ser alterado.")
        return redirect('pedido_detail', pedido_id=pedido.id)

    if request.method == 'POST':
        nova_qtd = int(request.POST.get('quantidade'))

        if item.tipo == 'ESTOQUE':

            # 🔥 1. DEVOLVE TUDO
            devolver_estoque(item)

            # 🔥 2. APAGA RELAÇÃO COM LOTES
            item.lotes.all().delete()

            # 🔥 3. BAIXA NOVAMENTE COM NOVA QUANTIDADE
            baixar_estoque(item.produto, nova_qtd, item)

        # ✔ atualiza quantidade
        item.quantidade = nova_qtd
        item.save()

    return redirect('pedido_detail', pedido_id=pedido.id)

@login_required
def itempedido_delete(request, id):
    item = get_object_or_404(ItemPedido, id=id)
    pedido = item.pedido

    # 🔒 regra de negócio
    if pedido.status != 'ABERTO':
        messages.error(request, "Pedido não pode ser alterado.")
        return redirect('pedido_detail', pedido_id=pedido.id)

    if request.method == 'POST':

        # 🔥 DEVOLVER AO ESTOQUE (SE FOR PRODUTO DE ESTOQUE)
        if item.tipo == 'ESTOQUE':
            devolver_estoque(item)

        item.delete()

    return redirect('pedido_detail', pedido_id=pedido.id)