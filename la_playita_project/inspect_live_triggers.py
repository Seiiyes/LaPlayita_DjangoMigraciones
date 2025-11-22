import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')
django.setup()

def inspect_triggers():
    with connection.cursor() as cursor:
        cursor.execute("SHOW TRIGGERS")
        triggers = cursor.fetchall()
        
        print(f"Encontrados {len(triggers)} triggers.")
        for trigger in triggers:
            name = trigger[0]
            table = trigger[2]
            statement = trigger[4]
            print(f"\nTrigger: {name} en Tabla: {table}")
            print("Statement:")
            print(statement)
            print("-" * 40)

if __name__ == "__main__":
    inspect_triggers()
