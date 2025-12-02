"""
Script de prueba para verificar que los reportes funcionen correctamente
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')
django.setup()

from django.db.models import Sum, Count, Avg, F, Q, Max, Min
from pos.models import Venta, VentaDetalle, Pago
from inventory.models import Producto, Lote, MovimientoInventario
from clients.models import Cliente
from django.utils import timezone
from datetime import timedelta

print("=" * 60)
print("PRUEBA DE REPORTES - LA PLAYITA")
print("=" * 60)

# Test Reporte de Ventas
print("\n1. REPORTE DE VENTAS")
print("-" * 60)
ventas = Venta.objects.all()
total_ventas = ventas.aggregate(total=Sum('total_venta'))['total'] or 0
cantidad_ventas = ventas.count()
print(f"✓ Total ventas: ${total_ventas:,.2f}")
print(f"✓ Cantidad ventas: {cantidad_ventas}")

ventas_por_metodo = Pago.objects.values('metodo_pago').annotate(
    total=Sum('monto'),
    cantidad=Count('id')
).order_by('-total')
print(f"✓ Ventas por método de pago: {ventas_por_metodo.count()} métodos")

productos_mas_vendidos = VentaDetalle.objects.values(
    'producto__nombre'
).annotate(
    cantidad_total=Sum('cantidad'),
    ingresos=Sum('subtotal')
).order_by('-cantidad_total')[:10]
print(f"✓ Top productos: {productos_mas_vendidos.count()} productos")

# Test Reporte de Inventario
print("\n2. REPORTE DE INVENTARIO")
print("-" * 60)
productos_stock_bajo = Producto.objects.filter(
    stock_actual__lte=F('stock_minimo')
).count()
print(f"✓ Productos con stock bajo: {productos_stock_bajo}")

fecha_limite = timezone.now().date() + timedelta(days=30)
lotes_por_vencer = Lote.objects.filter(
    fecha_caducidad__lte=fecha_limite,
    cantidad_disponible__gt=0
).count()
print(f"✓ Lotes próximos a vencer: {lotes_por_vencer}")

valor_inventario = Producto.objects.aggregate(
    valor_total=Sum(F('stock_actual') * F('precio_unitario'))
)['valor_total'] or 0
print(f"✓ Valor total inventario: ${valor_inventario:,.2f}")

hace_30_dias = timezone.now() - timedelta(days=30)
productos_con_movimiento = MovimientoInventario.objects.filter(
    fecha_movimiento__gte=hace_30_dias
).values_list('producto_id', flat=True).distinct().count()
print(f"✓ Productos con movimiento (30 días): {productos_con_movimiento}")

# Test Reporte de Clientes
print("\n3. REPORTE DE CLIENTES")
print("-" * 60)
clientes = Cliente.objects.exclude(id=1)
total_clientes = clientes.count()
print(f"✓ Total clientes: {total_clientes}")

top_clientes = clientes.annotate(
    total_compras=Sum('venta__total_venta'),
    cantidad_compras=Count('venta')
).filter(total_compras__isnull=False).order_by('-total_compras')[:20]
print(f"✓ Top clientes: {top_clientes.count()}")

clientes_nuevos = clientes.annotate(
    primera_compra=Min('venta__fecha_venta')
).filter(
    primera_compra__gte=hace_30_dias
).count()
print(f"✓ Clientes nuevos (30 días): {clientes_nuevos}")

hace_60_dias = timezone.now() - timedelta(days=60)
clientes_con_compras_recientes = Venta.objects.filter(
    fecha_venta__gte=hace_60_dias
).values_list('cliente_id', flat=True).distinct()
clientes_activos = clientes.filter(id__in=clientes_con_compras_recientes).count()
print(f"✓ Clientes activos (60 días): {clientes_activos}")

print("\n" + "=" * 60)
print("✓ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
print("=" * 60)
