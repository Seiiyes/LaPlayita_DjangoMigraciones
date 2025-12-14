#!/usr/bin/env python3
"""
Test final de configuración de correo para Railway
"""
import os
import sys
import django

# Configurar Django
sys.path.append('la_playita_project')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email_configuration():
    print("=== TEST DE CONFIGURACIÓN DE CORREO ===")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"EMAIL_PROVIDER: {getattr(settings, 'EMAIL_PROVIDER', 'No definido')}")
    print(f"DEBUG: {settings.DEBUG}")
    
    # Verificar si la contraseña está configurada
    if hasattr(settings, 'EMAIL_HOST_PASSWORD') and settings.EMAIL_HOST_PASSWORD:
        print(f"EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD)} (configurado)")
    else:
        print("EMAIL_HOST_PASSWORD: NO CONFIGURADO")
    
    print("\n=== ENVIANDO EMAIL DE PRUEBA ===")
    
    try:
        result = send_mail(
            subject='Test de correo - La Playita Railway',
            message='Este es un email de prueba desde Railway para verificar que SendGrid funciona correctamente.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['soporte.laplayita@gmail.com'],
            fail_silently=False,
        )
        
        if result == 1:
            print("✅ EMAIL ENVIADO EXITOSAMENTE")
            print("Revisa tu bandeja de entrada y los logs de SendGrid")
        else:
            print("❌ ERROR: send_mail retornó 0")
            
    except Exception as e:
        print(f"❌ ERROR AL ENVIAR EMAIL: {e}")
        print(f"Tipo de error: {type(e).__name__}")
        
        # Información adicional para debugging
        import traceback
        print("\nTraceback completo:")
        traceback.print_exc()

if __name__ == "__main__":
    test_email_configuration()