from datetime import date, timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ItemPedido, LoteProduto


@receiver(post_save, sender=ItemPedido)

