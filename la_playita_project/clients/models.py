from django.db import models
from django.conf import settings  # <--- Esta línea es clave

class Cliente(models.Model):

    nombres = models.CharField(max_length=50)
    apellidos = models.CharField(max_length=50)
    documento = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=25)
    correo = models.EmailField(max_length=60, unique=True)


    puntos_totales = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        db_table = 'cliente'
        managed = False

class ProductoCanjeble(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    puntos_requeridos = models.DecimalField(max_digits=10, decimal_places=2)
    stock_disponible = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'producto_canjeble'
        managed = True

class CanjeProducto(models.Model):
    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_COMPLETADO = 'completado'
    ESTADO_CANCELADO = 'cancelado'

    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_COMPLETADO, 'Completado'),
        (ESTADO_CANCELADO, 'Cancelado'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    producto = models.ForeignKey(ProductoCanjeble, on_delete=models.PROTECT)
    puntos_gastados = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_canje = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE)
    fecha_entrega = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Canje #{self.id} - {self.cliente}"

    class Meta:
        db_table = 'canje_producto'
        managed = True

class PuntosFidelizacion(models.Model):
    TIPO_GANANCIA = 'ganancia'
    TIPO_CANJE = 'canje'
    TIPO_AJUSTE = 'ajuste'

    TIPO_CHOICES = [
        (TIPO_GANANCIA, 'Ganancia por Compra'),
        (TIPO_CANJE, 'Canje de Producto'),
        (TIPO_AJUSTE, 'Ajuste Manual'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    puntos = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.CharField(max_length=255)
    fecha_transaccion = models.DateTimeField(auto_now_add=True)
    venta_id = models.IntegerField(null=True, blank=True)  # Referencia débil a Venta
    canje = models.ForeignKey(CanjeProducto, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.cliente} - {self.puntos} pts"

    class Meta:
        db_table = 'puntos_fidelizacion'
        managed = True



