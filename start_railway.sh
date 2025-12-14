#!/bin/bash

echo "=== INICIANDO APLICACIÓN EN RAILWAY ==="

cd /app/la_playita_project

echo "🎨 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "📁 Verificando archivos estáticos..."
ls -la staticfiles/ | head -5

echo "🔧 Ejecutando migraciones..."
python manage.py migrate --noinput || echo "⚠️ Algunas migraciones fallaron, continuando..."

echo "📧 Configuración lista..."

# Test automático de correo en Railway
echo "📤 Ejecutando test de correo SendGrid..."
python manage.py test_email --email soporte.laplayita@gmail.com || echo "⚠️ Test de correo falló"

echo "🚀 Iniciando servidor..."
gunicorn la_playita_project.wsgi:application --bind 0.0.0.0:${PORT:-8000} --timeout 120