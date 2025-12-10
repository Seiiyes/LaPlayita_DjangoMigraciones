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
    
    # Verificar conexión
    mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE -e "SELECT 1;" $DB_NAME
    if [ $? -eq 0 ]; then
        echo "Conexión exitosa a la base de datos"
        
        echo "🗑️ Limpiando base de datos existente..."
        
        # Deshabilitar verificaciones de claves foráneas temporalmente
        mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE -e "SET FOREIGN_KEY_CHECKS = 0;" $DB_NAME
        
        # Obtener lista de todas las tablas y eliminarlas
        TABLES=$(mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE -e "SELECT GROUP_CONCAT(table_name) FROM information_schema.tables WHERE table_schema='$DB_NAME';" -s -N $DB_NAME)
        
        if [ ! -z "$TABLES" ] && [ "$TABLES" != "NULL" ]; then
            echo "Eliminando tablas existentes: $TABLES"
            mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE -e "DROP TABLE $TABLES;" $DB_NAME
        else
            echo "No hay tablas para eliminar"
        fi
        
        # Rehabilitar verificaciones de claves foráneas
        mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE -e "SET FOREIGN_KEY_CHECKS = 1;" $DB_NAME
        
        echo "✅ Base de datos limpiada"
        
        echo "📥 Importando backup completo..."
        
        # Verificar si el archivo existe
        BACKUP_FILE=""
        if [ -f "/app/backup.sql" ]; then
            BACKUP_FILE="/app/backup.sql"
        elif [ -f "/app/database/ult_ver_backup_912.sql" ]; then
            BACKUP_FILE="/app/database/ult_ver_backup_912.sql"
        else
            echo "❌ Archivo de backup no encontrado"
            echo "Buscando archivos de backup disponibles..."
            find /app -name "*.sql" -type f
            exit 1
        fi
        
        echo "Procesando backup para compatibilidad con MySQL..."
        
        # Crear archivo temporal con correcciones de compatibilidad
        echo "Limpiando backup de elementos incompatibles..."
        
        # Usar awk para procesar el archivo y eliminar triggers/procedimientos problemáticos
        awk '
        BEGIN { skip = 0; in_trigger = 0; }
        
        # Detectar inicio de triggers o procedimientos
        /\/\*!50003 CREATE.*TRIGGER/ { skip = 1; in_trigger = 1; next }
        /\/\*!50003 CREATE.*PROCEDURE/ { skip = 1; next }
        /\/\*!50003 CREATE.*FUNCTION/ { skip = 1; next }
        /DELIMITER/ { skip = 1; next }
        
        # Detectar fin de triggers o procedimientos
        /\*\// && skip == 1 { 
            skip = 0; 
            in_trigger = 0; 
            next 
        }
        
        # Saltar líneas dentro de triggers/procedimientos
        skip == 1 { next }
        
        # Aplicar otras correcciones
        {
            gsub(/utf8mb4_uca1400_ai_ci/, "utf8mb4_unicode_ci")
            gsub(/utf8mb4_0900_ai_ci/, "utf8mb4_unicode_ci")
            gsub(/NO_AUTO_CREATE_USER,/, "")
            gsub(/,NO_AUTO_CREATE_USER/, "")
            gsub(/NO_AUTO_CREATE_USER/, "")
        }
        
        # Saltar líneas problemáticas
        /^CREATE DATABASE/ { next }
        /^USE `/ { next }
        /\/\*!50003 SET sql_mode/ { next }
        /\/\*!50017 DEFINER=/ { next }
        
        # Imprimir líneas válidas
        { print }
        ' "$BACKUP_FILE" > /tmp/backup_fixed.sql
        
        echo "Importando backup procesado..."
        mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE $DB_NAME < /tmp/backup_fixed.sql
        
        if [ $? -eq 0 ]; then
            echo "✅ Backup importado exitosamente"
            
            echo "🔧 Agregando campos necesarios para Django..."
            
            # Agregar columnas Django al usuario si no existen
            mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE -e "
            ALTER TABLE usuario 
            ADD COLUMN IF NOT EXISTS is_staff TINYINT(1) NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS is_superuser TINYINT(1) NOT NULL DEFAULT 0;
            " $DB_NAME
            
            # Crear tabla de sesiones Django
            mysql -h$DB_HOST -P$DB_PORT -u$DB_USER -p$DB_PASS --ssl=FALSE -e "
            CREATE TABLE IF NOT EXISTS django_session (
                session_key VARCHAR(40) NOT NULL PRIMARY KEY,
                session_data LONGTEXT NOT NULL,
                expire_date DATETIME(6) NOT NULL,
                KEY django_session_expire_date_a5c62663 (expire_date)
            );
            " $DB_NAME
            
            echo "✅ Campos Django agregados"
            
            echo "🔄 Sincronizando migraciones con Django..."
            python manage.py migrate --fake
            
            echo "✅ Importación completa finalizada"
        else
            echo "❌ Error al importar backup"
            exit 1
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