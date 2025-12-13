#!/usr/bin/env python3
"""
Script para probar correos directamente en Railway
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / 'la_playita_project'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')

try:
    django.setup()
    from django.core.mail import send_mail
    from django.conf import settings
    
    print("=== CONFIGURACIÓN ACTUAL ===")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_HOST_PASSWORD: {'***' if settings.EMAIL_HOST_PASSWORD else 'NO CONFIGURADO'}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"EMAIL_PROVIDER: {getattr(settings, 'EMAIL_PROVIDER', 'No definido')}")
    
    print("\n=== PRUEBA DE ENVÍO ===")
    
    # Usar tu email para la prueba
    test_email = "soporte.laplayita@gmail.com"  # Cambia por tu email
    
    try:
        result = send_mail(
            subject='PRUEBA RAILWAY - La Playita',
            message='Este es un correo de prueba desde Railway usando SendGrid.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False,
        )
        print(f"✅ Correo enviado exitosamente. Resultado: {result}")
        print(f"📧 Revisa tu bandeja: {test_email}")
        
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")
        print(f"Tipo de error: {type(e).__name__}")
        
        # Información adicional
        import traceback
        print("\n=== TRACEBACK ===")
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ Error al configurar Django: {e}")
    import traceback
    traceback.print_exc()