import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')
django.setup()

def check_tables():
    tables_to_check = ['puntos_fidelizacion', 'producto_canjeble', 'canje_producto']
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        print("Tablas encontradas:")
        for t in tables_to_check:
            if t in all_tables:
                print(f"[SI] {t}")
            else:
                print(f"[NO] {t}")

if __name__ == "__main__":
    check_tables()
