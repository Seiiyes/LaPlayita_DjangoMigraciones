"""
Utilidades para el módulo PQRS
"""
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def enviar_correo_respuesta(pqrs, respuesta):
    """
    Envía un correo al cliente con la respuesta del PQRS usando templates HTML elegantes
    """
    try:
        # Preparar contexto para los templates
        context = {
            'pqrs': pqrs,
            'respuesta': respuesta,
        }
        
        # Renderizar templates
        subject = f'Respuesta a su {pqrs.get_tipo_display()} - {pqrs.numero_caso}'
        html_content = render_to_string('pqrs/emails/respuesta_cliente.html', context)
        text_content = render_to_string('pqrs/emails/respuesta_cliente.txt', context)
        
        # Usar email verificado para mejor entregabilidad con Brevo
        from_email = "michaeldaramirez117@gmail.com"
        
        # Crear email con contenido alternativo
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[pqrs.cliente.correo]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Enviar email
        result = email.send(fail_silently=False)
        
        if result:
            logger.info(f"[PQRS] ✓ Email de respuesta enviado exitosamente para caso {pqrs.numero_caso} a {pqrs.cliente.correo}")
            return True
        else:
            logger.error(f"[PQRS] ✗ Error enviando email de respuesta para caso {pqrs.numero_caso}")
            return False
            
    except Exception as e:
        logger.error(f"[PQRS] ✗ Error al enviar correo de respuesta para caso {pqrs.numero_caso}: {e}", exc_info=True)
        return False


def enviar_correo_cambio_estado(pqrs, estado_anterior, estado_nuevo, observacion=None):
    """
    Envía un correo al cliente notificando el cambio de estado usando templates HTML elegantes
    """
    try:
        # Mapear estados para obtener la clave
        estado_map = {
            'Nuevo': 'nuevo',
            'En Proceso': 'en_proceso', 
            'Resuelto': 'resuelto',
            'Cerrado': 'cerrado'
        }
        
        estado_anterior_key = estado_map.get(estado_anterior, 'nuevo')
        
        # Preparar contexto para los templates
        context = {
            'pqrs': pqrs,
            'estado_anterior': estado_anterior,
            'estado_anterior_key': estado_anterior_key,
            'estado_nuevo': estado_nuevo,
            'observacion': observacion,
        }
        
        # Renderizar templates
        subject = f'Actualización de su {pqrs.get_tipo_display()} - {pqrs.numero_caso}'
        html_content = render_to_string('pqrs/emails/cambio_estado.html', context)
        text_content = render_to_string('pqrs/emails/cambio_estado.txt', context)
        
        # Usar email verificado para mejor entregabilidad con Brevo
        from_email = "michaeldaramirez117@gmail.com"
        
        # Crear email con contenido alternativo
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[pqrs.cliente.correo]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Enviar email
        result = email.send(fail_silently=False)
        
        if result:
            logger.info(f"[PQRS] ✓ Email de cambio de estado enviado exitosamente para caso {pqrs.numero_caso} a {pqrs.cliente.correo}")
            return True
        else:
            logger.error(f"[PQRS] ✗ Error enviando email de cambio de estado para caso {pqrs.numero_caso}")
            return False
            
    except Exception as e:
        logger.error(f"[PQRS] ✗ Error al enviar correo de cambio de estado para caso {pqrs.numero_caso}: {e}", exc_info=True)
        return False
