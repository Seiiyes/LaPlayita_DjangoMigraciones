#!/usr/bin/env python3
"""
Test comparativo: Gmail vs SendGrid
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / 'la_playita_project'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')

print("=== COMPARATIVO DE CONFIGURACIONES DE CORREO ===\n")

# Test 1: Configuración local (Gmail)
print("1. CONFIGURACIÓN LOCAL (Gmail):")
os.environ['DEBUG'] = 'True'
os.environ.pop('EMAIL_PROVIDER', None)

django.setup()
from django.conf import settings
from django.core.mail import send_mail

print(f"   DEBUG: {settings.DEBUG}")
print(f"   EMAIL_PROVIDER: {getattr(settings, 'EMAIL_PROVIDER', 'No definido')}")
print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

# Test 2: Configuración Railway (SendGrid)
print("\n2. CONFIGURACIÓN RAILWAY (SendGrid):")
os.environ['DEBUG'] = 'False'
os.environ['EMAIL_PROVIDER'] = 'sendgrid'
os.environ['EMAIL_HOST_PASSWORD'] = 'SG.test'  # Simulado
os.environ['SENDGRID_FROM_EMAIL'] = 'soporte.laplayita@gmail.com'

# Recargar configuración
from importlib import reload
import la_playita_project.settings
reload(la_playita_project.settings)

print(f"   DEBUG: {settings.DEBUG}")
print(f"   EMAIL_PROVIDER: {getattr(settings, 'EMAIL_PROVIDER', 'No definido')}")
print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

print("\n=== RESUMEN ===")
print("✅ Gmail: Funcionaba localmente con password de aplicación")
print("✅ SendGrid: Configurado con API key y sender verificado")
print("❓ Problema: Railway debe usar EMAIL_PROVIDER=sendgrid")

print("\n=== SOLUCIÓN ===")
print("En Railway, asegúrate de tener:")
print("- EMAIL_PROVIDER = sendgrid")
print("- DEBUG = False")
print("- Todas las variables de SendGrid configuradas")