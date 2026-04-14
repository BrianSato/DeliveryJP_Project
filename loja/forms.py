from django import forms
from .models import Cliente

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