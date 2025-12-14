"""
Backend de correo para Brevo (ex-Sendinblue) usando API HTTP
Evita el bloqueo de SMTP en Railway
"""
import requests
import logging
import base64
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


class BrevoEmailBackend(BaseEmailBackend):
    """
    Backend de correo que usa la API HTTP de Brevo
    """
    
    API_URL = "https://api.brevo.com/v3/smtp/email"
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'BREVO_API_KEY', '')
    
    def send_messages(self, email_messages):
        if not self.api_key:
            error_msg = "BREVO_API_KEY no configurado"
            logger.error(f"[BREVO] {error_msg}")
            if not self.fail_silently:
                raise Exception(error_msg)
            return 0
        
        num_sent = 0
        for message in email_messages:
            try:
                if self._send(message):
                    num_sent += 1
                    logger.info(f"[BREVO] ✓ Correo enviado a {', '.join(message.to)}")
            except Exception as e:
                logger.error(f"[BREVO] ✗ Error enviando correo: {e}")
                if not self.fail_silently:
                    raise
        
        return num_sent
    
    def _send(self, message):
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Preparar destinatarios
        to_list = [{"email": email} for email in message.to]
        
        # Preparar payload
        payload = {
            "sender": {"email": message.from_email or settings.DEFAULT_FROM_EMAIL},
            "to": to_list,
            "subject": message.subject,
        }
        
        # CC y BCC
        if message.cc:
            payload["cc"] = [{"email": email} for email in message.cc]
        if message.bcc:
            payload["bcc"] = [{"email": email} for email in message.bcc]
        
        # Manejar contenido HTML y texto para EmailMultiAlternatives
        if isinstance(message, EmailMultiAlternatives):
            # Buscar alternativa HTML
            html_content = None
            for content, mimetype in message.alternatives:
                if mimetype == 'text/html':
                    html_content = content
                    break
            
            if html_content:
                payload["htmlContent"] = html_content
                payload["textContent"] = message.body  # Texto plano como fallback
            else:
                payload["textContent"] = message.body
                
            # Manejar adjuntos (como imágenes del logo)
            if hasattr(message, 'attachments') and message.attachments:
                attachments = []
                for attachment in message.attachments:
                    try:
                        # Para MIMEImage y otros adjuntos
                        if hasattr(attachment, 'get_payload'):
                            content = attachment.get_payload(decode=True)
                            filename = attachment.get_filename() or "attachment"
                            if content:
                                attachments.append({
                                    "name": filename,
                                    "content": base64.b64encode(content).decode('utf-8')
                                })
                                logger.info(f"[BREVO] Adjunto procesado: {filename}")
                    except Exception as e:
                        logger.warning(f"[BREVO] No se pudo procesar adjunto: {e}")
                
                if attachments:
                    payload["attachment"] = attachments
        else:
            # Detectar si el body es HTML
            if hasattr(message, 'content_subtype') and message.content_subtype == 'html':
                payload["htmlContent"] = message.body
            else:
                payload["textContent"] = message.body
        
        # Log del envío
        logger.info(f"[BREVO] Enviando correo a {', '.join(message.to)} - Asunto: {message.subject}")
        
        try:
            response = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"[BREVO] ✓ API respondió exitosamente: {response.status_code}")
                return True
            else:
                error_msg = f"Brevo API error: {response.status_code} - {response.text}"
                logger.error(f"[BREVO] ✗ {error_msg}")
                if not self.fail_silently:
                    raise Exception(error_msg)
                return False
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Error de conexión con Brevo API: {e}"
            logger.error(f"[BREVO] ✗ {error_msg}")
            if not self.fail_silently:
                raise Exception(error_msg)
            return False
