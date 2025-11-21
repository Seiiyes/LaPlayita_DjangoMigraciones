from django.db import models
from django.utils import timezone


class Categoria(models.Model):
    nombre = models.CharField(max_length=25)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'categoria'
        managed = False


class Producto(models.Model):
    nombre = models.CharField(unique=True, max_length=50)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    costo_promedio = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Costo promedio ponderado, calculado automáticamente.")
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    stock_minimo = models.PositiveIntegerField(default=10)
    stock_actual = models.PositiveIntegerField(default=0, help_text="Calculado automáticamente a partir de los lotes.")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, default=1)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'producto'
        managed = False


class Lote(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    reabastecimiento_detalle = models.ForeignKey('suppliers.ReabastecimientoDetalle', on_delete=models.CASCADE, null=True, blank=True)
    numero_lote = models.CharField(max_length=50)
    cantidad_disponible = models.PositiveIntegerField()
    costo_unitario_lote = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_caducidad = models.DateField()
    fecha_entrada = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Lote {self.numero_lote} ({self.producto.nombre})"

    class Meta:
        db_table = 'lote'
        managed = False
        unique_together = (('producto', 'numero_lote'),)


class MovimientoInventario(models.Model):
    producto = models.ForeignKey(Producto, models.DO_NOTHING)
    lote = models.ForeignKey(Lote, models.SET_NULL, blank=True, null=True)
    cantidad = models.IntegerField()
    tipo_movimiento = models.CharField(max_length=20)
    # SQL uses current_timestamp default; use auto_now_add to mimic existing default on insert
    fecha_movimiento = models.DateTimeField(default=timezone.now)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    # Referencias a venta y reabastecimiento según el dump SQL
    venta = models.ForeignKey('pos.Venta', models.SET_NULL, blank=True, null=True)
    reabastecimiento = models.ForeignKey('suppliers.Reabastecimiento', models.SET_NULL, blank=True, null=True)

    class Meta:
        db_table = 'movimiento_inventario'
        managed = False