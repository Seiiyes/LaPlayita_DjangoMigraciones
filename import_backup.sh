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
            python manage.py migrate --fake
            
            echo "Verificando estructura de tabla usuario..."
            
            # Verificar si is_staff existe
            IS_STAFF_EXISTS=$(mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE -e "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='$DB_NAME' AND table_name='usuario' AND column_name='is_staff';" -s -N $DB_NAME)
            
            if [ "$IS_STAFF_EXISTS" -eq 0 ]; then
                echo "Agregando columna is_staff..."
                mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE -e "ALTER TABLE usuario ADD COLUMN is_staff TINYINT(1) NOT NULL DEFAULT 0;" $DB_NAME
            else
                echo "Columna is_staff ya existe"
            fi
            
            # Verificar si is_superuser existe
            IS_SUPERUSER_EXISTS=$(mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE -e "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='$DB_NAME' AND table_name='usuario' AND column_name='is_superuser';" -s -N $DB_NAME)
            
            if [ "$IS_SUPERUSER_EXISTS" -eq 0 ]; then
                echo "Agregando columna is_superuser..."
                mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE -e "ALTER TABLE usuario ADD COLUMN is_superuser TINYINT(1) NOT NULL DEFAULT 0;" $DB_NAME
            else
                echo "Columna is_superuser ya existe"
            fi
            
            echo "Verificando roles en la base de datos..."
            
            # Verificar si existe el rol Vendedor
            VENDEDOR_EXISTS=$(mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE -e "SELECT COUNT(*) FROM rol WHERE nombre='Vendedor';" -s -N $DB_NAME)
            
            if [ "$VENDEDOR_EXISTS" -eq 0 ]; then
                echo "Creando rol Vendedor..."
                mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE -e "INSERT INTO rol (nombre) VALUES ('Vendedor');" $DB_NAME
            else
                echo "Rol Vendedor ya existe"
            fi
            
            # Verificar si existe el rol Administrador
            ADMIN_EXISTS=$(mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE -e "SELECT COUNT(*) FROM rol WHERE nombre='Administrador';" -s -N $DB_NAME)
            
            if [ "$ADMIN_EXISTS" -eq 0 ]; then
                echo "Creando rol Administrador..."
                mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE -e "INSERT INTO rol (nombre) VALUES ('Administrador');" $DB_NAME
            else
                echo "Rol Administrador ya existe"
            fi
            
            echo "✅ Estructura de tabla usuario y roles verificados"-initial
            
            # Marcar todas las migraciones de clients como fake ya que las tablas existen
            echo "Marcando migraciones de clients como aplicadas..."
            python manage.py migrate clients --fake
            
            echo "✅ Migraciones sincronizadas"
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