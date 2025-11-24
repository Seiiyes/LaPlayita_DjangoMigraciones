import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # Verificar si la columna ya existe
    cursor.execute("""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'producto_canjeble' AND COLUMN_NAME = 'producto_inventario_id'
    """)
    result = cursor.fetchone()
    
    if result:
        print("La columna ya existe")
    else:
        # Agregar la columna
        cursor.execute("""
        ALTER TABLE producto_canjeble 
        ADD COLUMN producto_inventario_id INT NULL
        """)
        print("Columna agregada exitosamente")
