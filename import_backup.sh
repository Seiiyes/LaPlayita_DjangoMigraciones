#!/bin/bash

echo "=== Iniciando proceso de importación de backup ==="

cd /app/la_playita_project

# Extraer datos de conexión de DATABASE_URL
if [ ! -z "$DATABASE_URL" ]; then
    echo "DATABASE_URL encontrada, parseando conexión..."
    
    # Parsear DATABASE_URL: mysql://user:password@host:port/database
    DB_USER=$(echo $DATABASE_URL | sed 's/mysql:\/\/\([^:]*\):.*/\1/')
    DB_PASS=$(echo $DATABASE_URL | sed 's/mysql:\/\/[^:]*:\([^@]*\)@.*/\1/')
    DB_HOST=$(echo $DATABASE_URL | sed 's/.*@\([^:]*\):.*/\1/')
    DB_PORT=$(echo $DATABASE_URL | sed 's/.*:\([0-9]*\)\/.*/\1/')
    DB_NAME=$(echo $DATABASE_URL | sed 's/.*\/\([^?]*\).*/\1/')
    
    echo "Conectando a: $DB_HOST:$DB_PORT como $DB_USER"
    
    # Verificar conexión (deshabilitar SSL para Railway)
    mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE -e "SELECT 1;" $DB_NAME
    if [ $? -eq 0 ]; then
        echo "Conexión exitosa a la base de datos"
        
        # Verificar si las tablas ya existen
        TABLE_COUNT=$(mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$DB_NAME';" -s -N $DB_NAME)
        
        if [ "$TABLE_COUNT" -eq 0 ] || [ "$TABLE_COUNT" -lt 10 ]; then
            echo "Base de datos vacía o incompleta. Importando backup..."
            mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE $DB_NAME < /app/database/ult_ver_backup_912.sql
            
            if [ $? -eq 0 ]; then
                echo "✅ Backup importado exitosamente"
                
                # Ejecutar migraciones fake para las tablas existentes
                echo "Sincronizando migraciones existentes..."
                python manage.py migrate --fake-initial
                
                # Ejecutar migraciones reales para las nuevas tablas del sistema de fidelización
                echo "Aplicando migraciones del sistema de fidelización..."
                python manage.py migrate clients 0004_create_loyalty_tables
                python manage.py migrate clients 0005_add_cliente_foreignkeys
                
                echo "✅ Todas las migraciones completadas"
            else
                echo "❌ Error al importar backup"
                exit 1
            fi
        else
            echo "Base de datos ya contiene $TABLE_COUNT tablas. Saltando importación."
            echo "Ejecutando migraciones fake para sincronizar..."
            python manage.py migrate --fake-initial
            
            # Marcar las migraciones del sistema de fidelización como aplicadas si las tablas ya existen
            echo "Verificando tablas del sistema de fidelización..."
            LOYALTY_TABLES=$(mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$DB_NAME' AND table_name IN ('producto_canjeble', 'canje_producto', 'puntos_fidelizacion');" -s -N $DB_NAME)
            
            if [ "$LOYALTY_TABLES" -gt 0 ]; then
                echo "Tablas del sistema de fidelización ya existen. Marcando migraciones como aplicadas..."
                python manage.py migrate clients 0004_create_loyalty_tables --fake
                python manage.py migrate clients 0005_add_cliente_foreignkeys --fake
            else
                echo "Aplicando migraciones del sistema de fidelización..."
                python manage.py migrate clients
            fi
        fi
    else
        echo "Error de conexión a la base de datos"
        exit 1
    fi
else
    echo "DATABASE_URL no encontrada"
    echo "Ejecutando migraciones normales..."
    python manage.py migrate
fi

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "Iniciando servidor..."
gunicorn la_playita_project.wsgi:application --bind 0.0.0.0:${PORT:-8000}