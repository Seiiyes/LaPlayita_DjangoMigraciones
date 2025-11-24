import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')
django.setup()

from django.db import connection

print("Creando tablas de permisos...")

try:
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuario_groups (
              id bigint NOT NULL AUTO_INCREMENT,
              usuario_id bigint NOT NULL,
              group_id int NOT NULL,
              PRIMARY KEY (id),
              UNIQUE KEY usuario_groups_unique (usuario_id,group_id)
            ) ENGINE=InnoDB
        """)
        print("Tabla usuario_groups creada")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuario_user_permissions (
              id bigint NOT NULL AUTO_INCREMENT,
              usuario_id bigint NOT NULL,
              permission_id int NOT NULL,
              PRIMARY KEY (id),
              UNIQUE KEY usuario_permissions_unique (usuario_id,permission_id)
            ) ENGINE=InnoDB
        """)
        print("Tabla usuario_user_permissions creada")
        print("Listo!")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
