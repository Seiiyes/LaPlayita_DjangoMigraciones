from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .models import Lote, Producto

@receiver(post_delete, sender=Lote)
def actualizar_stock_producto_on_lote_delete(sender, instance, **kwargs):
    """

@receiver(post_save, sender=Lote)
def actualizar_stock_producto_on_lote_save(sender, instance, created, **kwargs):
    """