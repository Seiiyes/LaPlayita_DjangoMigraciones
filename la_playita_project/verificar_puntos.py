import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')
django.setup()

from clients.models import PuntosFidelizacion, Cliente

def verificar_puntos():
    print("=== Verificando Puntos de Fidelización ===\n")
    
    # Verificar últimas transacciones
    transacciones = PuntosFidelizacion.objects.all().order_by('-fecha_transaccion')[:10]
    print(f"Total de transacciones: {PuntosFidelizacion.objects.count()}")
    print(f"\nÚltimas 10 transacciones:")
    for t in transacciones:
        print(f"- Cliente: {t.cliente.nombres} | Puntos: {t.puntos} | Tipo: {t.tipo} | Fecha: {t.fecha_transaccion}")
    
    # Verificar puntos de clientes
    print("\n=== Puntos por Cliente ===")
    clientes = Cliente.objects.exclude(id=1).order_by('-puntos_totales')[:5]
    for c in clientes:
        print(f"- {c.nombres} {c.apellidos}: {c.puntos_totales} puntos")

if __name__ == "__main__":
    verificar_puntos()
