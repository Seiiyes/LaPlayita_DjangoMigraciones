"""
Backend de correo personalizado para Resend usando API HTTP
Evita el bloqueo de SMTP en Railway
"""
import resend
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class ResendEmailBackend(BaseEmailBackend):
    """
    Backend de correo que usa la API HTTP de Resend
    en lugar de SMTP para evitar bloqueos en Railway
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'RESEND_API_KEY', '')
        
        if self.api_key:
            resend.api_key = self.api_key
    
    def send_messages(self, email_messages):
        """
        Envía uno o más mensajes de correo usando la API de Resend
        """
        if not self.api_key:
            if not self.fail_silently:
                raise Exception("RESEND_API_KEY no configurado")
            return 0
        
        num_sent = 0
        for message in email_messages:
            try:
                sent = self._send(message)
                if sent:
                    num_sent += 1
            except Exception as e:
                if not self.fail_silently:
                    raise
        
        return num_sent
    
    def _send(self, message):
        """
        Envía un mensaje individual usando la API de Resend
        """
        try:
            # Preparar el contenido
            params = {
                "from": message.from_email or settings.DEFAULT_FROM_EMAIL,
                "to": list(message.to),
                "subject": message.subject,
            }
            
            # Agregar CC y BCC si existen
            if message.cc:
                params["cc"] = list(message.cc)
            if message.bcc:
                params["bcc"] = list(message.bcc)
            
            # Determinar si es HTML o texto plano
            if hasattr(message, 'content_subtype') and message.content_subtype == 'html':
                params["html"] = message.body
            else:
                params["text"] = message.body
            
            # Enviar usando la API de Resend
            response = resend.Emails.send(params)
            
            return True
            
        except Exception as e:
            if not self.fail_silently:
                raise
            return False
