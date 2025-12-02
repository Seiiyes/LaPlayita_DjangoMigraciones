from django.db import models
from django.utils import timezone
from django.conf import settings


class Proveedor(models.Model):
    class TipoDocumento(models.TextChoices):
        NIT = 'NIT', 'NIT'
        RUT = 'RUT', 'RUT'
        CEDULA_CIUDADANIA = 'CC', 'Cédula de Ciudadanía'
        CEDULA_EXTRANJERIA = 'CE', 'Cédula de Extranjería'
        PASAPORTE = 'PAS', 'Pasaporte'

    tipo_documento = models.CharField(
        max_length=3,
        choices=TipoDocumento.choices,
        default=TipoDocumento.NIT,
    )
    documento_identificacion = models.CharField(max_length=20, unique=True)
    nombre_empresa = models.CharField(max_length=100)
    telefono = models.CharField(max_length=50)
    correo = models.CharField(max_length=50)
    direccion = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre_empresa

    class Meta:
        managed = False
        db_table = 'proveedor'


class Reabastecimiento(models.Model):
    ESTADO_BORRADOR = 'borrador'
    ESTADO_SOLICITADO = 'solicitado'
    ESTADO_RECIBIDO = 'recibido'
    ESTADO_CANCELADO = 'cancelado'

    ESTADO_CHOICES = [
        (ESTADO_BORRADOR, 'Borrador'),
        (ESTADO_SOLICITADO, 'Solicitado'),
        (ESTADO_RECIBIDO, 'Recibido'),
        (ESTADO_CANCELADO, 'Cancelado'),
    ]

    FORMA_PAGO_TRANSFERENCIA = 'transferencia'
    FORMA_PAGO_EFECTIVO = 'efectivo'
    FORMA_PAGO_CHEQUE = 'cheque'
    FORMA_PAGO_PSE = 'pse'
    FORMA_PAGO_TARJETA_CREDITO = 'tarjeta_credito'
    FORMA_PAGO_CONSIGNACION = 'consignacion'

    FORMA_PAGO_CHOICES = [
        (FORMA_PAGO_TRANSFERENCIA, 'Transferencia Bancaria'),
        (FORMA_PAGO_EFECTIVO, 'Efectivo'),
        (FORMA_PAGO_CHEQUE, 'Cheque'),
        (FORMA_PAGO_PSE, 'PSE'),
        (FORMA_PAGO_TARJETA_CREDITO, 'Tarjeta de Crédito'),
        (FORMA_PAGO_CONSIGNACION, 'Consignación Bancaria'),
    ]

    fecha = models.DateTimeField(default=timezone.now)
    costo_total = models.DecimalField(max_digits=12, decimal_places=2)
    iva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_SOLICITADO)
    forma_pago = models.CharField(max_length=25, choices=FORMA_PAGO_CHOICES, default=FORMA_PAGO_EFECTIVO)
    observaciones = models.TextField(blank=True, null=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)

    class Meta:
        managed = False
        db_table = 'reabastecimiento'


class ReabastecimientoDetalle(models.Model):
    reabastecimiento = models.ForeignKey(Reabastecimiento, models.CASCADE)
    producto = models.ForeignKey('inventory.Producto', on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    cantidad_recibida = models.IntegerField(default=0)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    iva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_caducidad = models.DateField(null=True, blank=True)
    
    # Auditoría
    recibido_por = models.ForeignKey('users.Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='reabastecimiento_detalles_recibidos')
    fecha_recepcion = models.DateTimeField(null=True, blank=True)
    cantidad_anterior = models.IntegerField(default=0)  # Para auditoría de cambios
    numero_lote = models.CharField(max_length=100, null=True, blank=True)  # Número de lote/serial

    class Meta:
        managed = False
        db_table = 'reabastecimiento_detalle'


class AuditoriaReabastecimiento(models.Model):
    ACCIONES = [
        ('creado', 'Creado'),
        ('recibido', 'Recibido'),
        ('editado', 'Editado'),
        ('cancelado', 'Cancelado'),
    ]
    
    reabastecimiento = models.ForeignKey(Reabastecimiento, on_delete=models.CASCADE, related_name='auditorias')
    usuario = models.ForeignKey('users.Usuario', on_delete=models.SET_NULL, null=True)
    accion = models.CharField(max_length=20, choices=ACCIONES)
    cantidad_anterior = models.IntegerField(null=True, blank=True)
    cantidad_nueva = models.IntegerField(null=True, blank=True)
    descripcion = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        managed = False
        db_table = 'auditoria_reabastecimiento'
        ordering = ['-fecha']