from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    #home
    path('', views.home, name='home'),
    #login
    path('login/', views.MyloginView.as_view(),name='login'),
    # clientes menu
    path('cliente/', views.cliente_menu, name='cliente_menu'),
    # cliente novo
    path('cliente/novo/', views.cliente_create, name='cliente_create'),
    # lista de clientes
    path('cliente/lista/', views.cliente_list, name='cliente_list'),
    #detalhes dos clientes
    path('cliente/<int:id>/', views.cliente_detail, name='cliente_detail'),
]