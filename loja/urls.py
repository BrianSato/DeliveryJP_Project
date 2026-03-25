from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    #home
    path('', views.home, name='home'),
    #login
    path(
        'login/',
         auth_views.LoginView.as_view(
             template_name='loja/login.html',
             redirect_authenticated_user=True
         ),
        name='login'
    ),
    # clientes menu
    path('cliente/', views.cliente_menu, name='cliente_menu'),
    # cliente novo
    path('cliente/novo/', views.cliente_create, name='cliente_create'),
    # lista de clientes
    path('cliente/lista/', views.cliente_list, name='cliente_list'),
    #detalhes dos clientes
    path('cliente/<int:id>/', views.cliente_detail, name='cliente_detail'),
    # menu de produtos
    path('produto/', views.produto_menu, name='produto_menu'),
    # produto novo
    path('produto/novo/', views.produto_create, name='produto_create'),
    #lista de produtos
    path('produto/lista/', views.produto_list, name='produto_list'),
    #detalhes do produto
    path('produto/<int:id>/', views.produto_detail, name='produto_detail'),
]