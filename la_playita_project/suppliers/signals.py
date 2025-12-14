"""
Signals para el módulo de proveedores.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Reabastecimiento
from .views import send_supply_request_email
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Reabastecimiento)
def enviar_correo_solicitud(sender, instance, created, **kwargs):
    """
    Signal deshabilitado para evitar correos duplicados.
    Los correos se envían manualmente desde las vistas después de guardar los detalles.
    """
    # Signal deshabilitado para evitar duplicados
    # Los correos se manejan desde las vistas
    pass
