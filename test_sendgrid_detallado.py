#!/usr/bin/env python3
"""
Test detallado de SendGrid con logging
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

# Configuración SendGrid
SMTP_HOST = "smtp.sendgrid.net"
SMTP_PORT = 587
SMTP_USER = "apikey"
SMTP_PASS = input("Ingresa la API key de SendGrid: ").strip()
FROM_EMAIL = "soporte.laplayita@gmail.com"
TO_EMAIL = input("Ingresa tu email para la prueba: ").strip() or "soporte.laplayita@gmail.com"

print("=== PRUEBA DETALLADA DE SENDGRID ===")
print(f"Host: {SMTP_HOST}")
print(f"Puerto: {SMTP_PORT}")
print(f"Usuario: {SMTP_USER}")
print(f"Desde: {FROM_EMAIL}")
print(f"Para: {TO_EMAIL}")

try:
    # Crear mensaje
    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL
    msg['Subject'] = "Prueba detallada SendGrid - La Playita"
    
    body = """
    Este es un correo de prueba detallado para verificar SendGrid.
    
    Si recibes este correo, SendGrid está funcionando correctamente.
    
    Saludos,
    Sistema La Playita
    """
    msg.attach(MIMEText(body, 'plain'))
    
    # Conectar con logging detallado
    print("\n=== CONECTANDO A SENDGRID ===")
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.set_debuglevel(1)  # Habilitar debug detallado
    
    print("Iniciando TLS...")
    server.starttls()
    
    print("Autenticando...")
    server.login(SMTP_USER, SMTP_PASS)
    
    print("✅ Conexión y autenticación exitosa")
    
    print("Enviando correo...")
    text = msg.as_string()
    result = server.sendmail(FROM_EMAIL, TO_EMAIL, text)
    server.quit()
    
    print("✅ Correo enviado exitosamente")
    print(f"📧 Revisa tu bandeja: {TO_EMAIL}")
    print(f"Resultado: {result}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Tipo: {type(e).__name__}")
    
    import traceback
    print("\n=== TRACEBACK COMPLETO ===")
    traceback.print_exc()