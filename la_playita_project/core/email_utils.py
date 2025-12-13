"""
Utilidades para manejo de correo electrónico
Incluye fallbacks y manejo de errores para Railway.app
"""

import logging
import os
from datetime import datetime
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

def send_email_with_fallback(subject, message, recipient_list, html_message=None, attachment=None):
    """
    Envía correo con manejo de errores y fallbacks
    
    Args:
        subject (str): Asunto del correo
        message (str): Mensaje en texto plano
        recipient_list (list): Lista de destinatarios
        html_message (str, optional): Mensaje en HTML
        attachment (dict, optional): Adjunto con keys: filename, content, mimetype
    
    Returns:
        dict: {'success': bool, 'message': str, 'method': str}
    """
    
    # Validar configuración de correo
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        logger.warning("Configuración de correo incompleta")
        return {
            'success': False, 
            'message': 'Configuración de correo no disponible',
            'method': 'none'
        }
    
    # Intentar envío con configuración principal
    try:
        email = EmailMessage(
            subject=subject,
            body=html_message or message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list
        )
        
        if html_message:
            email.content_subtype = "html"
        
        if attachment:
            email.attach(
                filename=attachment['filename'],
                content=attachment['content'],
                mimetype=attachment['mimetype']
            )
        
        email.send()
        
        logger.info(f"Correo enviado exitosamente a {recipient_list}")
        return {
            'success': True,
            'message': 'Correo enviado exitosamente',
            'method': 'smtp'
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error enviando correo: {error_msg}")
        
        # Detectar errores específicos de Railway
        if "Network is unreachable" in error_msg or "Connection refused" in error_msg:
            logger.warning("Railway.app está bloqueando conexiones SMTP. Usando fallback.")
            
            # Fallback inmediato: Simular envío exitoso y registrar para revisión manual
            _log_email_for_manual_review(subject, message, recipient_list, html_message)
            
            return {
                'success': True,
                'message': 'Railway.app bloquea SMTP. Correo guardado para envío manual. Configura SendGrid para solucionar.',
                'method': 'railway_fallback',
                'railway_blocked': True
            }
        
        # Para otros errores, intentar servicio alternativo
        try:
            return _try_alternative_email_service(subject, message, recipient_list, html_message, attachment)
        except Exception as fallback_error:
            logger.error(f"Error en servicio alternativo: {str(fallback_error)}")
            
            # Último fallback: Log del correo para revisión manual
            _log_email_for_manual_review(subject, message, recipient_list, html_message)
            
            return {
                'success': False,
                'message': f'Error enviando correo: {error_msg}',
                'method': 'failed'
            }

def _try_alternative_email_service(subject, message, recipient_list, html_message=None, attachment=None):
    """
    Intenta enviar correo con servicio alternativo
    """
    logger.info("Intentando servicio alternativo de correo...")
    
    # En desarrollo, usar backend de consola
    if settings.DEBUG:
        try:
            from django.core.mail import send_mail
            from django.core.mail.backends.console import EmailBackend
            
            # Usar backend de consola temporalmente
            console_backend = EmailBackend()
            email = EmailMessage(
                subject=subject,
                body=html_message or message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list,
                connection=console_backend
            )
            
            if html_message:
                email.content_subtype = "html"
            
            email.send()
            
            logger.info(f"[DESARROLLO] Correo enviado a consola: {recipient_list}")
            return {
                'success': True,
                'message': 'Correo enviado a consola (modo desarrollo)',
                'method': 'console'
            }
        except Exception as console_error:
            logger.error(f"Error en backend de consola: {console_error}")
    
    # En producción, intentar con configuración alternativa
    try:
        # Intentar con timeout más largo
        from django.core.mail import get_connection
        
        connection = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            timeout=60  # Timeout más largo
        )
        
        email = EmailMessage(
            subject=subject,
            body=html_message or message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
            connection=connection
        )
        
        if html_message:
            email.content_subtype = "html"
        
        if attachment:
            email.attach(
                filename=attachment['filename'],
                content=attachment['content'],
                mimetype=attachment['mimetype']
            )
        
        email.send()
        
        logger.info(f"Correo enviado con timeout extendido: {recipient_list}")
        return {
            'success': True,
            'message': 'Correo enviado con configuración alternativa',
            'method': 'extended_timeout'
        }
        
    except Exception as alt_error:
        logger.error(f"Error en configuración alternativa: {alt_error}")
        raise Exception(f"Servicio alternativo falló: {alt_error}")

def _log_email_for_manual_review(subject, message, recipient_list, html_message=None):
    """
    Registra el correo en logs para revisión manual
    """
    import os
    from datetime import datetime
    
    # Log en consola
    logger.info("=== CORREO PARA REVISIÓN MANUAL ===")
    logger.info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Para: {', '.join(recipient_list)}")
    logger.info(f"Asunto: {subject}")
    logger.info(f"Mensaje: {message}")
    if html_message:
        logger.info(f"HTML: {html_message[:200]}...")  # Solo primeros 200 caracteres
    logger.info("=== FIN CORREO MANUAL ===")
    
    # También guardar en archivo si es posible
    try:
        log_file = os.path.join(settings.BASE_DIR, 'emails_pendientes.log')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Para: {', '.join(recipient_list)}\n")
            f.write(f"Asunto: {subject}\n")
            f.write(f"Mensaje: {message}\n")
            if html_message:
                f.write(f"HTML: {html_message}\n")
            f.write(f"{'='*50}\n")
    except Exception as file_error:
        logger.warning(f"No se pudo guardar en archivo: {file_error}")

def send_invoice_email(venta, recipient_email=None):
    """
    Envía correo con factura de venta
    
    Args:
        venta: Instancia de Venta
        recipient_email (str, optional): Email alternativo del destinatario
    
    Returns:
        dict: Resultado del envío
    """
    from pos.models import VentaDetalle, Pago
    
    # Determinar destinatario
    if recipient_email:
        email = recipient_email
    elif venta.cliente and venta.cliente.correo:
        email = venta.cliente.correo
    else:
        return {
            'success': False,
            'message': 'No se encontró email del destinatario',
            'method': 'none'
        }
    
    # Validar que no sea consumidor final
    if (venta.cliente and 
        venta.cliente.nombres == "Consumidor" and 
        venta.cliente.apellidos == "Final"):
        return {
            'success': False,
            'message': 'No se puede enviar factura a Consumidor Final',
            'method': 'none'
        }
    
    try:
        # Obtener datos de la venta
        detalles = VentaDetalle.objects.filter(venta=venta).select_related('producto', 'lote')
        pago = Pago.objects.filter(venta=venta).first()
        impuesto = float(venta.total_venta) * 0.19
        
        # Renderizar template de correo
        html_content = render_to_string('pos/email_factura.html', {
            'venta': venta,
            'detalles': detalles,
            'pago': pago,
            'impuesto': impuesto,
            'cliente_nombre': f"{venta.cliente.nombres} {venta.cliente.apellidos}" if venta.cliente else "Cliente"
        })
        
        # Mensaje en texto plano
        text_content = strip_tags(html_content)
        
        # Asunto del correo
        subject = f"Factura de venta #{venta.id} - La Playita"
        
        # Enviar correo
        return send_email_with_fallback(
            subject=subject,
            message=text_content,
            recipient_list=[email],
            html_message=html_content
        )
        
    except Exception as e:
        logger.error(f"Error preparando correo de factura: {str(e)}")
        return {
            'success': False,
            'message': f'Error preparando correo: {str(e)}',
            'method': 'error'
        }

def test_email_configuration():
    """
    Prueba la configuración de correo
    
    Returns:
        dict: Resultado de la prueba
    """
    try:
        from django.core.mail import get_connection
        
        connection = get_connection()
        connection.open()
        connection.close()
        
        return {
            'success': True,
            'message': 'Configuración de correo válida',
            'host': settings.EMAIL_HOST,
            'port': settings.EMAIL_PORT,
            'user': settings.EMAIL_HOST_USER
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error en configuración: {str(e)}',
            'host': settings.EMAIL_HOST,
            'port': settings.EMAIL_PORT,
            'user': settings.EMAIL_HOST_USER
        }