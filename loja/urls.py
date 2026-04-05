from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
#login
    path(
        'login/',
         auth_views.LoginView.as_view(
             template_name='loja/login.html',
             redirect_authenticated_user=True
         ),
        name='login'
    ),
    #home
    path('', views.home, name='home'),
    # lista de produtos vencendo
    path('estoque_vencendo', views.produtos_vencendo, name='estoque_vencendo'),
    #lista de produtos vencidos
    path('estoque_vencidos', views.produtos_vencidos, name='estoque_vencidos'),
    # lista de clientes
    path('cliente/', views.cliente_list, name='cliente_list'),
    # cliente novo
    path('cliente/novo/', views.cliente_create, name='cliente_create'),
    #detalhes dos clientes
    path('cliente/<int:id>/', views.cliente_detail, name='cliente_detail'),
    # menu de produtos
    path('produto/', views.produto_menu, name='produto_menu'),
    # produto novo
    path('produto/novo/', views.produto_create, name='produto_create'),
    #lista de produtos no estoque
    path('produto/lista_estoque/', views.produto_estoque_list, name='produto_estoque_list'),
    # lista de produtos encomendados
    path('produto/lista_encomenda/', views.produto_encomenda_list, name='produto_encomenda_list'),
    #detalhes do produto
    path('produto/<int:id>/', views.produto_detail, name='produto_detail'),
    #criar lote do produto
    path('lote/novo/<int:produto_id>/', views.lote_create, name='lote_create'),
    #lista de pedidos
    path('pedido/lista/', views.pedido_list, name='pedido_list'),
    #detalhes do pedido
    path('pedido/<int:pedido_id>/', views.pedido_detail, name='pedido_detail'),
    #criar novo pedido
    path('pedido/novo/', views.pedido_create, name='pedido_create'),
    #detalhes da encomenda
    path('pedido/encomenda/<int:pedido_id>/', views.pedido_encomenda_detail, name='pedido_encomenda_detail'),
]