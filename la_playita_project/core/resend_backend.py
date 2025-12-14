"""
Backend de correo personalizado para Resend usando API HTTP
Evita el bloqueo de SMTP en Railway
Usa requests directamente sin dependencias adicionales
"""
import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class ResendEmailBackend(BaseEmailBackend):
    """
    Backend de correo que usa la API HTTP de Resend
    en lugar de SMTP para evitar bloqueos en Railway
    """
    
    API_URL = "https://api.resend.com/emails"
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'RESEND_API_KEY', '')
    
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
        Envía un mensaje individual usando la API HTTP de Resend
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Preparar el payload
        payload = {
            "from": message.from_email or settings.DEFAULT_FROM_EMAIL,
            "to": list(message.to),
            "subject": message.subject,
        }
        
        # Agregar CC y BCC si existen
        if message.cc:
            payload["cc"] = list(message.cc)
        if message.bcc:
            payload["bcc"] = list(message.bcc)
        
        # Determinar si es HTML o texto plano
        if hasattr(message, 'content_subtype') and message.content_subtype == 'html':
            payload["html"] = message.body
        else:
            payload["text"] = message.body
        
        # Enviar usando requests
        response = requests.post(
            self.API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return True
        else:
            error_msg = f"Resend API error: {response.status_code} - {response.text}"
            if not self.fail_silently:
                raise Exception(error_msg)
            return False
