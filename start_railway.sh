#!/bin/bash

echo "=== INICIANDO APLICACIÓN EN RAILWAY ==="

cd /app/la_playita_project

echo "🎨 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "📁 Verificando archivos estáticos..."
ls -la staticfiles/ | head -5

echo "🔧 Ejecutando migraciones..."
python manage.py migrate --noinput || echo "⚠️ Algunas migraciones fallaron, continuando..."

echo "📧 Probando configuración de correos..."
python test_email_startup.py

echo "🚀 Iniciando servidor..."
gunicorn la_playita_project.wsgi:application --bind 0.0.0.0:${PORT:-8000} --timeout 120