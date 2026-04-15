from django import forms
from .models import Cliente, Produto


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'telefone','endereco']

        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do cliente'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Telefone'
            }),
        }

class ProdutoEstoqueForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome_produto', 'preco_unitario']