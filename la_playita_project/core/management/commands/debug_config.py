from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Debug configuración de correos'

    def handle(self, *args, **options):
        self.stdout.write('=== DEBUG CONFIGURACIÓN ===')
        self.stdout.write(f'EMAIL_HOST: {settings.EMAIL_HOST}')
        self.stdout.write(f'EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'EMAIL_HOST_PASSWORD: {settings.EMAIL_HOST_PASSWORD[:10] if settings.EMAIL_HOST_PASSWORD else "VACIO"}...')
        self.stdout.write(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
        
        # Test de envío
        from django.core.mail import send_mail
        try:
            result = send_mail(
                'Test Debug Railway',
                'Test desde comando debug',
                settings.DEFAULT_FROM_EMAIL,
                ['soporte.laplayita@gmail.com'],
                fail_silently=False,
            )
            self.stdout.write(f'✅ Correo enviado: {result}')
        except Exception as e:
            self.stdout.write(f'❌ Error: {e}')