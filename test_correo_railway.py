#!/usr/bin/env python3
"""
Test de correo para Railway sin API keys en el código
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / 'la_playita_project'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')

# Simular entorno Railway
os.environ['RAILWAY_ENVIRONMENT'] = 'production'
os.environ['DEBUG'] = 'False'

try:
    django.setup()
    from django.core.mail import send_mail
    from django.conf import settings
    
    print("=== CONFIGURACIÓN EN RAILWAY ===")
    print(f"DEBUG: {settings.DEBUG}")
    print(f"EMAIL_PROVIDER: {getattr(settings, 'EMAIL_PROVIDER', 'No definido')}")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    print("\n=== VARIABLES DE ENTORNO RAILWAY ===")
    railway_vars = ['RAILWAY_ENVIRONMENT', 'EMAIL_PROVIDER', 'EMAIL_HOST', 'EMAIL_HOST_USER', 'SENDGRID_FROM_EMAIL']
    for var in railway_vars:
        value = os.environ.get(var, 'NO DEFINIDO')
        print(f"{var}: {value}")
    
    print(f"\n=== PRUEBA DE ENVÍO ===")
    print("Nota: Esta prueba usa las variables de entorno de Railway")
    
except Exception as e:
    print(f"❌ Error al configurar Django: {e}")
    import traceback
    traceback.print_exc()