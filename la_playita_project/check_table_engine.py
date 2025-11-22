import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')
django.setup()

def check_table_status():
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLE STATUS WHERE Name = 'cliente'")
        row = cursor.fetchone()
        if row:
            print(f"Tabla: {row[0]}")
            print(f"Engine: {row[1]}")
            print(f"Collation: {row[14]}")
        else:
            print("Tabla 'cliente' no encontrada.")

if __name__ == "__main__":
    check_table_status()
