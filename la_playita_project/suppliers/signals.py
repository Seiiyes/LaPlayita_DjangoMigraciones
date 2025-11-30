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
    Envía un correo al proveedor cuando se crea una nueva solicitud de reabastecimiento.
    """
    if created and instance.estado == Reabastecimiento.ESTADO_SOLICITADO:
        logger.info(f"[SIGNAL] Enviando correo para reabastecimiento {instance.id}")
        try:
            result = send_supply_request_email(instance, None)
            logger.info(f"[SIGNAL] Correo enviado: {result}")
        except Exception as e:
            logger.error(f"[SIGNAL] Error al enviar correo: {e}", exc_info=True)
