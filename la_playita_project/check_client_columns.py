import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')
django.setup()

def check_columns():
    with connection.cursor() as cursor:
        cursor.execute("DESCRIBE cliente")
        columns = cursor.fetchall()
        print("Columnas en 'cliente':")
        for col in columns:
            print(f"- {col[0]} ({col[1]})")

if __name__ == "__main__":
    check_columns()
