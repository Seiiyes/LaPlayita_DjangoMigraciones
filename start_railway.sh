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

# Test de correo opcional (solo si TEST_EMAIL=true)
if [ "$TEST_EMAIL" = "true" ]; then
    echo "📤 Ejecutando test de correo..."
    python manage.py test_email || echo "⚠️ Test de correo falló"
fi

echo "🚀 Iniciando servidor..."
gunicorn la_playita_project.wsgi:application --bind 0.0.0.0:${PORT:-8000} --timeout 120