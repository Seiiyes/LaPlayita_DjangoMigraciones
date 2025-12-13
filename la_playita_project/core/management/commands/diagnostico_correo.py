from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Diagnóstico completo de correos'

    def handle(self, *args, **options):
        self.stdout.write('=== DIAGNÓSTICO COMPLETO DE CORREOS ===')
        
        # Configuración actual
        self.stdout.write('\n1. CONFIGURACIÓN DJANGO:')
        self.stdout.write(f'   DEBUG: {settings.DEBUG}')
        self.stdout.write(f'   EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'   EMAIL_HOST: {settings.EMAIL_HOST}')
        self.stdout.write(f'   EMAIL_PORT: {settings.EMAIL_PORT}')
        self.stdout.write(f'   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'   EMAIL_HOST_PASSWORD: {"***" if settings.EMAIL_HOST_PASSWORD else "NO CONFIGURADO"}')
        self.stdout.write(f'   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'   EMAIL_PROVIDER: {getattr(settings, "EMAIL_PROVIDER", "No definido")}')
        
        # Variables de entorno
        self.stdout.write('\n2. VARIABLES DE ENTORNO:')
        env_vars = ['DEBUG', 'EMAIL_PROVIDER', 'EMAIL_HOST', 'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD', 'SENDGRID_FROM_EMAIL']
        for var in env_vars:
            value = os.environ.get(var, 'NO DEFINIDO')
            if 'PASSWORD' in var and value != 'NO DEFINIDO':
                value = '***'
            self.stdout.write(f'   {var}: {value}')
        
        # Prueba de envío
        self.stdout.write('\n3. PRUEBA DE ENVÍO:')
        try:
            result = send_mail(
                subject='Diagnóstico Railway - La Playita',
                message='Este correo confirma que el sistema de correos funciona correctamente.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['soporte.laplayita@gmail.com'],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'   ✅ Correo enviado exitosamente. Resultado: {result}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error al enviar correo: {e}'))
            self.stdout.write(f'   Tipo de error: {type(e).__name__}')
            
            # Traceback completo
            import traceback
            self.stdout.write('\n4. TRACEBACK COMPLETO:')
            self.stdout.write(traceback.format_exc())
        
        self.stdout.write('\n=== FIN DEL DIAGNÓSTICO ===')