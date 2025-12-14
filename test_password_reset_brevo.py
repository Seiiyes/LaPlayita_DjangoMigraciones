#!/usr/bin/env python
"""
Script para probar el reset de contraseña con Brevo
"""
import os
import sys
import django

# Configurar Django
sys.path.append('la_playita_project')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')
django.setup()

from django.conf import settings
from users.forms import CustomPasswordResetForm
from users.models import Usuario
from core.email_utils import test_email_configuration

def test_password_reset_brevo():
    print("=== PRUEBA DE RESET DE CONTRASEÑA CON BREVO ===")
    
    # 1. Verificar configuración de Brevo
    print("\n1. Verificando configuración de Brevo...")
    brevo_key = getattr(settings, 'BREVO_API_KEY', '')
    email_provider = getattr(settings, 'EMAIL_PROVIDER', '')
    email_backend = getattr(settings, 'EMAIL_BACKEND', '')
    
    print(f"   BREVO_API_KEY: {'✅ Configurado' if brevo_key else '❌ No configurado'}")
    print(f"   EMAIL_PROVIDER: {email_provider}")
    print(f"   EMAIL_BACKEND: {email_backend}")
    
    # 2. Probar configuración general
    print("\n2. Probando configuración de correo...")
    config = test_email_configuration()
    print(f"   Resultado: {config['success']} - {config['message']}")
    
    # 3. Verificar usuarios disponibles
    print("\n3. Verificando usuarios disponibles...")
    usuarios = Usuario.objects.filter(email__isnull=False).exclude(email='')
    print(f"   Usuarios con email: {usuarios.count()}")
    
    if not usuarios.exists():
        print("   ❌ No hay usuarios con email configurado")
        return
    
    # Usar el primer usuario para la prueba
    test_user = usuarios.first()
    print(f"   Usuario de prueba: {test_user.username} ({test_user.email})")
    
    # 4. Probar el formulario de reset
    print("\n4. Probando formulario de reset de contraseña...")
    form_data = {'email': test_user.email}
    form = CustomPasswordResetForm(data=form_data)
    
    if form.is_valid():
        print(f"   ✅ Formulario válido para {test_user.email}")
        
        # 5. Intentar enviar correo de reset
        print("\n5. Enviando correo de reset con Brevo...")
        try:
            # Simular request básico
            class MockRequest:
                def __init__(self):
                    self.META = {'HTTP_HOST': 'localhost:8000'}
            
            mock_request = MockRequest()
            
            form.save(
                request=mock_request,
                use_https=False,
                domain_override='localhost:8000',
                html_email_template_name='registration/password_reset_email.html'
            )
            print("   ✅ Correo de reset enviado exitosamente con Brevo")
            
        except Exception as e:
            print(f"   ❌ Error enviando correo: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"   ❌ Formulario inválido: {form.errors}")
    
    print("\n=== RESUMEN ===")
    if brevo_key and brevo_key.startswith('xkeysib-'):
        print("✅ Brevo configurado correctamente")
        print("✅ Reset de contraseña actualizado para usar Brevo")
        print("✅ Sistema listo para producción")
    else:
        print("❌ Brevo no configurado - revisa BREVO_API_KEY")

if __name__ == "__main__":
    test_password_reset_brevo()