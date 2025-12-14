#!/usr/bin/env python3
"""
Script de diagnóstico para verificar configuración de correo en Railway
"""
import os
import sys
import django

# Configurar Django
sys.path.append('la_playita_project')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail

def diagnosticar_configuracion():
    print("=== DIAGNÓSTICO DE CONFIGURACIÓN DE CORREO EN RAILWAY ===")
    print()
    
    # Variables de entorno
    print("🔧 VARIABLES DE ENTORNO:")
    env_vars = [
        'DEBUG', 'EMAIL_PROVIDER', 'EMAIL_HOST', 'EMAIL_PORT', 
        'EMAIL_USE_TLS', 'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD',
        'DEFAULT_FROM_EMAIL', 'RAILWAY_ENVIRONMENT'
    ]
    
    for var in env_vars:
        value = os.environ.get(var, 'NO DEFINIDA')
        if var == 'EMAIL_HOST_PASSWORD' and value != 'NO DEFINIDA':
            value = f"{'*' * (len(value) - 4)}{value[-4:]}"
        print(f"  {var}: {value}")
    
    print()
    
    # Configuración de Django
    print("⚙️ CONFIGURACIÓN DE DJANGO:")
    print(f"  DEBUG: {settings.DEBUG}")
    print(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    if hasattr(settings, 'EMAIL_HOST_PASSWORD') and settings.EMAIL_HOST_PASSWORD:
        print(f"  EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD)} (configurado)")
    else:
        print("  EMAIL_HOST_PASSWORD: NO CONFIGURADO")
    
    print()
    
    # Verificar si estamos usando SendGrid
    email_provider = getattr(settings, 'EMAIL_PROVIDER', 'No definido')
    print(f"📧 PROVEEDOR DE EMAIL: {email_provider}")
    
    if email_provider == 'sendgrid':
        print("✅ SendGrid está configurado como proveedor")
    else:
        print("❌ SendGrid NO está configurado como proveedor")
        print("   Verifica que EMAIL_PROVIDER=sendgrid en Railway")
    
    print()
    
    # Test de envío
    print("📤 PROBANDO ENVÍO DE EMAIL...")
    
    try:
        result = send_mail(
            subject='[RAILWAY TEST] Diagnóstico de correo - La Playita',
            message=f'''
Este es un email de prueba desde Railway.

Configuración detectada:
- EMAIL_PROVIDER: {email_provider}
- EMAIL_HOST: {settings.EMAIL_HOST}
- EMAIL_BACKEND: {settings.EMAIL_BACKEND}
- DEBUG: {settings.DEBUG}

Si recibes este correo, la configuración está funcionando correctamente.
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['soporte.laplayita@gmail.com'],
            fail_silently=False,
        )
        
        if result == 1:
            print("✅ EMAIL ENVIADO EXITOSAMENTE")
            print("   Revisa tu bandeja de entrada y los logs de SendGrid Activity")
        else:
            print("❌ ERROR: send_mail retornó 0 (no se envió)")
            
    except Exception as e:
        print(f"❌ ERROR AL ENVIAR EMAIL: {e}")
        print(f"   Tipo de error: {type(e).__name__}")
        
        # Información adicional
        import traceback
        print("\n📋 TRACEBACK COMPLETO:")
        traceback.print_exc()
    
    print()
    print("=== FIN DEL DIAGNÓSTICO ===")

if __name__ == "__main__":
    diagnosticar_configuracion()