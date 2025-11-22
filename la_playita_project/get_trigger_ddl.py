import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')
django.setup()

def show_create_trigger():
    with connection.cursor() as cursor:
        cursor.execute("SHOW CREATE TRIGGER trg_lote_after_update")
        row = cursor.fetchone()
        print(row[2]) # SQL Original Statement

if __name__ == "__main__":
    show_create_trigger()
