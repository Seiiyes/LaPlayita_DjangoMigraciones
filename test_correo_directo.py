#!/usr/bin/env python3
"""
Test directo de correos usando las mismas configuraciones que Railway
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django con las mismas variables que Railway
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / 'la_playita_project'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')

# Simular entorno Railway
os.environ['DEBUG'] = 'False'
os.environ['EMAIL_PROVIDER'] = 'sendgrid'
os.environ['EMAIL_HOST'] = 'smtp.sendgrid.net'
os.environ['EMAIL_HOST_USER'] = 'apikey'
os.environ['EMAIL_HOST_PASSWORD'] = 'TU_API_KEY_AQUI'  # Usar variable de entorno
os.environ['EMAIL_PORT'] = '587'
os.environ['EMAIL_USE_TLS'] = 'True'
os.environ['SENDGRID_FROM_EMAIL'] = 'soporte.laplayita@gmail.com'

try:
    django.setup()
    from django.core.mail import send_mail
    from django.conf import settings
    
    print("=== CONFIGURACIÓN SIMULANDO RAILWAY ===")
    print(f"DEBUG: {settings.DEBUG}")
    print(f"EMAIL_PROVIDER: {getattr(settings, 'EMAIL_PROVIDER', 'No definido')}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    print("\n=== ENVIANDO CORREO DE PRUEBA ===")
    
    # Cambiar por tu email personal para la prueba
    test_email = input("Ingresa tu email para la prueba (o presiona Enter para usar soporte.laplayita@gmail.com): ").strip()
    if not test_email:
        test_email = "soporte.laplayita@gmail.com"
    
    try:
        result = send_mail(
            subject='Prueba SendGrid - La Playita (Simulando Railway)',
            message='Este correo confirma que SendGrid funciona con la configuración de Railway.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False,
        )
        print(f"✅ Correo enviado exitosamente. Resultado: {result}")
        print(f"📧 Revisa tu bandeja: {test_email}")
        
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")
        print(f"Tipo de error: {type(e).__name__}")
        
        import traceback
        print("\n=== TRACEBACK ===")
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ Error al configurar Django: {e}")
    import traceback
    traceback.print_exc()