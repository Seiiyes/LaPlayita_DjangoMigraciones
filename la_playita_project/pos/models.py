from django.db import models
from django.utils import timezone
from django.conf import settings


class Venta(models.Model):
    fecha_venta = models.DateTimeField(default=timezone.now)
    canal_venta = models.CharField(max_length=20, default='Tienda')
    cliente = models.ForeignKey('clients.Cliente', on_delete=models.PROTECT)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, models.PROTECT)
    pedido = models.ForeignKey('Pedido', null=True, blank=True, on_delete=models.SET_NULL, db_column='pedido_id')
    total_venta = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        managed = False
        db_table = 'venta'

class VentaDetalle(models.Model):
    venta = models.ForeignKey(Venta, models.CASCADE)
    producto = models.ForeignKey('inventory.Producto', models.DO_NOTHING)
    lote = models.ForeignKey('inventory.Lote', models.DO_NOTHING)
    cantidad = models.IntegerField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'venta_detalle'


# --- Pedidos Models ---
class Pedido(models.Model):
    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_EN_PREPARACION = 'en_preparacion'
    ESTADO_LISTO_PARA_ENTREGA = 'listo_para_entrega'
    ESTADO_COMPLETADO = 'completado'
    ESTADO_CANCELADO = 'cancelado'

    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_EN_PREPARACION, 'En Preparación'),
        (ESTADO_LISTO_PARA_ENTREGA, 'Listo para Entrega'),
        (ESTADO_COMPLETADO, 'Completado'),
        (ESTADO_CANCELADO, 'Cancelado'),
    ]

    cliente = models.ForeignKey('clients.Cliente', on_delete=models.PROTECT)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, help_text="Empleado que registra el pedido.")
    fecha_creacion = models.DateTimeField(default=timezone.now, db_column='fecha_pedido')
    fecha_entrega_estimada = models.DateTimeField(null=True, blank=True)

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, db_column='total_pedido')
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente}"

    class Meta:
        managed = False
        db_table = 'pedido'

class PedidoDetalle(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey('inventory.Producto', on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, help_text="Precio del producto al momento de crear el pedido.")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en Pedido #{self.pedido.id}"

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    class Meta:
        managed = False
        db_table = 'pedido_detalle'


class Pago(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=25)
    fecha_pago = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, default='completado')
    referencia_transaccion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pago'


class Mesa(models.Model):
    ESTADO_DISPONIBLE = 'disponible'
    ESTADO_OCUPADA = 'ocupada'
    ESTADO_RESERVADA = 'reservada'
    
    ESTADO_CHOICES = [
        (ESTADO_DISPONIBLE, 'Disponible'),
        (ESTADO_OCUPADA, 'Ocupada'),
        (ESTADO_RESERVADA, 'Reservada'),
    ]
    
    numero = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=50, blank=True)
    capacidad = models.PositiveIntegerField(default=4)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_DISPONIBLE)
    activa = models.BooleanField(default=True)
    
    # Campos para la cuenta actual
    cuenta_abierta = models.BooleanField(default=False)
    total_cuenta = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    fecha_apertura = models.DateTimeField(null=True, blank=True)
    cliente = models.ForeignKey('clients.Cliente', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Mesa {self.numero} - {self.get_estado_display()}"
    
    class Meta:
        db_table = 'mesa'
        ordering = ['numero']


class ItemMesa(models.Model):
    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey('inventory.Producto', on_delete=models.PROTECT)
    lote = models.ForeignKey('inventory.Lote', on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_agregado = models.DateTimeField(default=timezone.now)
    facturado = models.BooleanField(default=False)
    anotacion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} - Mesa {self.mesa.numero}"
    
    class Meta:
        db_table = 'item_mesa'