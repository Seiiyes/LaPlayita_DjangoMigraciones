"""
Script de prueba para verificar la funcionalidad de descarte de lotes
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')
django.setup()

from inventory.models import Lote, MovimientoInventario, Producto
from datetime import date

def test_descarte_lote():
    print("=" * 80)
    print("PRUEBA DE FUNCIONALIDAD: DESCARTE DE LOTES")
    print("=" * 80)
    
    # Buscar un lote con stock disponible
    lotes_disponibles = Lote.objects.filter(cantidad_disponible__gt=0).select_related('producto')[:5]
    
    if not lotes_disponibles:
        print("\n❌ No hay lotes con stock disponible para probar.")
        return
    
    print(f"\n📦 Lotes disponibles para descarte: {lotes_disponibles.count()}")
    print("\n" + "-" * 80)
    
    for i, lote in enumerate(lotes_disponibles, 1):
        dias_restantes = (lote.fecha_caducidad - date.today()).days
        estado = "🟢 Vigente" if dias_restantes > 7 else "🟡 Por vencer" if dias_restantes > 0 else "🔴 Vencido"
        
        print(f"\n{i}. Lote: {lote.numero_lote}")
        print(f"   Producto: {lote.producto.nombre}")
        print(f"   Cantidad disponible: {lote.cantidad_disponible} unidades")
        print(f"   Costo unitario: ${lote.costo_unitario_lote}")
        print(f"   Fecha caducidad: {lote.fecha_caducidad.strftime('%d/%m/%Y')}")
        print(f"   Estado: {estado} ({dias_restantes} días)")
    
    print("\n" + "=" * 80)
    print("VERIFICACIÓN DE MOVIMIENTOS DE DESCARTE")
    print("=" * 80)
    
    # Verificar si hay movimientos de descarte
    movimientos_descarte = MovimientoInventario.objects.filter(tipo_movimiento='descarte')
    total_descarte = movimientos_descarte.count()
    
    print(f"\n📊 Total de movimientos de descarte registrados: {total_descarte}")
    
    if total_descarte > 0:
        print("\n📋 Últimos 5 descartes:")
        print("-" * 80)
        
        for mov in movimientos_descarte.order_by('-fecha_movimiento')[:5]:
            print(f"\n🗑️  Descarte #{mov.id}")
            print(f"   Producto: {mov.producto.nombre}")
            print(f"   Lote: {mov.lote.numero_lote if mov.lote else 'N/A'}")
            print(f"   Cantidad: {abs(mov.cantidad)} unidades")
            print(f"   Fecha: {mov.fecha_movimiento.strftime('%d/%m/%Y %H:%M:%S')}")
            print(f"   Descripción: {mov.descripcion}")
    else:
        print("\n✅ No hay descartes registrados aún.")
        print("   Puede probar la funcionalidad desde el admin de Django:")
        print("   1. Ir a Admin > Inventario > Lotes")
        print("   2. Seleccionar un lote")
        print("   3. Usar la acción 'Descartar productos del lote seleccionado'")
    
    print("\n" + "=" * 80)
    print("ESTADÍSTICAS DE MOVIMIENTOS")
    print("=" * 80)
    
    # Estadísticas generales
    total_movimientos = MovimientoInventario.objects.count()
    entradas = MovimientoInventario.objects.filter(tipo_movimiento='entrada').count()
    salidas = MovimientoInventario.objects.filter(tipo_movimiento='salida').count()
    descartes = MovimientoInventario.objects.filter(tipo_movimiento='descarte').count()
    
    print(f"\n📈 Total de movimientos: {total_movimientos}")
    print(f"   • Entradas: {entradas}")
    print(f"   • Salidas (ventas): {salidas}")
    print(f"   • Descartes: {descartes}")
    
    if total_movimientos > 0:
        print(f"\n📊 Distribución:")
        print(f"   • Entradas: {entradas/total_movimientos*100:.1f}%")
        print(f"   • Salidas: {salidas/total_movimientos*100:.1f}%")
        print(f"   • Descartes: {descartes/total_movimientos*100:.1f}%")
    
    print("\n" + "=" * 80)
    print("PRODUCTOS CON DESCARTES")
    print("=" * 80)
    
    # Productos que han tenido descartes
    productos_con_descarte = (MovimientoInventario.objects
        .filter(tipo_movimiento='descarte')
        .values('producto__nombre')
        .distinct())
    
    if productos_con_descarte:
        print(f"\n📦 Productos con descartes registrados: {productos_con_descarte.count()}")
        for p in productos_con_descarte:
            producto_nombre = p['producto__nombre']
            total_descartado = (MovimientoInventario.objects
                .filter(tipo_movimiento='descarte', producto__nombre=producto_nombre)
                .aggregate(total=Sum('cantidad'))['total'] or 0)
            
            print(f"   • {producto_nombre}: {abs(total_descartado)} unidades descartadas")
    else:
        print("\n✅ Ningún producto ha tenido descartes aún.")
    
    print("\n" + "=" * 80)
    print("INSTRUCCIONES DE USO")
    print("=" * 80)
    
    print("""
Para descartar productos de un lote:

1. DESDE EL ADMIN DE DJANGO:
   a. Acceder a: http://localhost:8000/admin/
   b. Ir a: Inventario > Lotes
   c. Seleccionar el lote deseado (checkbox)
   d. En "Acción": Seleccionar "🗑️ Descartar productos del lote seleccionado"
   e. Click en "Ir"
   f. Completar el formulario:
      - Cantidad a descartar
      - Motivo (daño, vencimiento, accidente, etc.)
      - Observaciones (opcional)
   g. Click en "Confirmar Descarte"

2. DESDE LA LISTA DE LOTES:
   También puede hacer click directamente en un lote y usar el botón de descarte.

3. VERIFICACIÓN:
   - El stock del lote se actualizará automáticamente
   - Se creará un movimiento de inventario tipo "descarte"
   - Se registrará la fecha, motivo y observaciones

MOTIVOS DISPONIBLES:
   • Producto dañado
   • Producto vencido
   • Accidente / Rotura
   • Problema de calidad
   • Robo / Pérdida
   • Otro motivo
    """)
    
    print("\n" + "=" * 80)
    print("PRUEBA COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    test_descarte_lote()
