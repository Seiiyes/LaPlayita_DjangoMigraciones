"""
Backend de correo para Brevo (ex-Sendinblue) usando API HTTP
Evita el bloqueo de SMTP en Railway
"""
import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


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
            if not self.fail_silently:
                raise Exception("BREVO_API_KEY no configurado")
            return 0
        
        num_sent = 0
        for message in email_messages:
            try:
                if self._send(message):
                    num_sent += 1
            except Exception as e:
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
        
        # HTML o texto
        if hasattr(message, 'content_subtype') and message.content_subtype == 'html':
            payload["htmlContent"] = message.body
        else:
            payload["textContent"] = message.body
        
        response = requests.post(
            self.API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            return True
        else:
            if not self.fail_silently:
                raise Exception(f"Brevo API error: {response.status_code} - {response.text}")
            return False
