"""
Utilidades para el módulo PQRS
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def enviar_correo_respuesta(pqrs, respuesta):
    """
    Envía un correo al cliente con la respuesta del PQRS
    """
    subject = f'Respuesta a su {pqrs.get_tipo_display()} - {pqrs.numero_caso}'
    
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <h2 style="color: #0066cc; border-bottom: 2px solid #0066cc; padding-bottom: 10px;">
                La Playita - Respuesta a su {pqrs.get_tipo_display()}
            </h2>
            
            <p>Estimado/a <strong>{pqrs.cliente.nombres} {pqrs.cliente.apellidos}</strong>,</p>
            
            <p>Le informamos que hemos procesado su {pqrs.get_tipo_display().lower()} con número de caso <strong>{pqrs.numero_caso}</strong>.</p>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #0066cc; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #0066cc;">Respuesta:</h3>
                <p style="white-space: pre-wrap;">{respuesta}</p>
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background-color: #f9f9f9; border-radius: 5px;">
                <h4 style="margin-top: 0;">Detalles de su caso:</h4>
                <ul style="list-style: none; padding: 0;">
                    <li><strong>Número de caso:</strong> {pqrs.numero_caso}</li>
                    <li><strong>Tipo:</strong> {pqrs.get_tipo_display()}</li>
                    <li><strong>Estado:</strong> {pqrs.get_estado_display()}</li>
                    <li><strong>Fecha de registro:</strong> {pqrs.fecha_creacion.strftime('%d/%m/%Y %H:%M')}</li>
                </ul>
            </div>
            
            <p style="margin-top: 20px;">Si tiene alguna pregunta adicional, no dude en contactarnos.</p>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            
            <p style="font-size: 12px; color: #666;">
                <strong>La Playita</strong><br>
                Este es un correo automático, por favor no responda a este mensaje.
            </p>
        </div>
    </body>
    </html>
    """
    
    plain_message = strip_tags(html_message)
    
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [pqrs.cliente.correo]
    
    try:
        send_mail(
            subject,
            plain_message,
            from_email,
            recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False


def enviar_correo_cambio_estado(pqrs, estado_anterior, estado_nuevo, observacion):
    """
    Envía un correo al cliente notificando el cambio de estado
    """
    subject = f'Actualización de su {pqrs.get_tipo_display()} - {pqrs.numero_caso}'
    
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <h2 style="color: #0066cc; border-bottom: 2px solid #0066cc; padding-bottom: 10px;">
                La Playita - Actualización de Estado
            </h2>
            
            <p>Estimado/a <strong>{pqrs.cliente.nombres} {pqrs.cliente.apellidos}</strong>,</p>
            
            <p>Le informamos que el estado de su {pqrs.get_tipo_display().lower()} <strong>{pqrs.numero_caso}</strong> ha sido actualizado.</p>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #0066cc; margin: 20px 0;">
                <p style="margin: 0;">
                    <strong>Estado anterior:</strong> {estado_anterior}<br>
                    <strong>Estado actual:</strong> <span style="color: #0066cc; font-weight: bold;">{estado_nuevo}</span>
                </p>
            </div>
            
            <p>Continuaremos trabajando en su caso para brindarle la mejor solución posible.</p>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            
            <p style="font-size: 12px; color: #666;">
                <strong>La Playita</strong><br>
                Este es un correo automático, por favor no responda a este mensaje.
            </p>
        </div>
    </body>
    </html>
    """
    
    plain_message = strip_tags(html_message)
    
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [pqrs.cliente.correo]
    
    try:
        send_mail(
            subject,
            plain_message,
            from_email,
            recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False
