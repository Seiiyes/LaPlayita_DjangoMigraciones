import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')
django.setup()

from pos.models import Venta, VentaDetalle
from inventory.models import Producto, Lote

def verify_last_sale():
    try:
        last_sale = Venta.objects.last()
        if not last_sale:
            print("No se encontraron ventas.")
            return

        print(f"Última Venta ID: {last_sale.id}")
        print(f"Fecha: {last_sale.fecha_venta}")
        print(f"Total: {last_sale.total_venta}")
        
        detalles = VentaDetalle.objects.filter(venta=last_sale)
        print(f"\nDetalles ({detalles.count()} items):")
        for d in detalles:
            print(f"- {d.producto.nombre} x {d.cantidad} (Lote: {d.lote.numero_lote})")
            
        print("\n¡Venta registrada exitosamente!")
        
    except Exception as e:
        print(f"Error verificando venta: {e}")

if __name__ == "__main__":
    verify_last_sale()
