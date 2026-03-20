from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Venda,Pagamento

@receiver(post_save, sender=Venda)
def criar_pagamento(sender, instance,created,**kwargs):
    if created:
        Pagamento.objects.create(venda=instance)