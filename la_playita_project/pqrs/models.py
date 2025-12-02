from django.db import models
from django.conf import settings
from django.utils import timezone

class Pqrs(models.Model):
    TIPO_PETICION = 'peticion'
    TIPO_QUEJA = 'queja'
    TIPO_RECLAMO = 'reclamo'
    TIPO_SUGERENCIA = 'sugerencia'

    TIPO_CHOICES = [
        (TIPO_PETICION, 'Petición'),
        (TIPO_QUEJA, 'Queja'),
        (TIPO_RECLAMO, 'Reclamo'),
        (TIPO_SUGERENCIA, 'Sugerencia'),
    ]

    CATEGORIA_GENERAL = 'general'
    CATEGORIA_PRODUCTO = 'producto'
    CATEGORIA_SERVICIO = 'servicio'
    CATEGORIA_ENTREGA = 'entrega'

    CATEGORIA_CHOICES = [
        (CATEGORIA_GENERAL, 'General'),
        (CATEGORIA_PRODUCTO, 'Producto'),
        (CATEGORIA_SERVICIO, 'Servicio'),
        (CATEGORIA_ENTREGA, 'Entrega'),
    ]

    PRIORIDAD_BAJA = 'baja'
    PRIORIDAD_MEDIA = 'media'
    PRIORIDAD_ALTA = 'alta'
    PRIORIDAD_URGENTE = 'urgente'

    PRIORIDAD_CHOICES = [
        (PRIORIDAD_BAJA, 'Baja'),
        (PRIORIDAD_MEDIA, 'Media'),
        (PRIORIDAD_ALTA, 'Alta'),
        (PRIORIDAD_URGENTE, 'Urgente'),
    ]

    ESTADO_NUEVO = 'nuevo'
    ESTADO_EN_PROCESO = 'en_proceso'
    ESTADO_RESUELTO = 'resuelto'
    ESTADO_CERRADO = 'cerrado'

    ESTADO_CHOICES = [
        (ESTADO_NUEVO, 'Nuevo'),
        (ESTADO_EN_PROCESO, 'En Proceso'),
        (ESTADO_RESUELTO, 'Resuelto'),
        (ESTADO_CERRADO, 'Cerrado'),
    ]

    numero_caso = models.CharField(max_length=20, unique=True, editable=False)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, default=CATEGORIA_GENERAL)
    prioridad = models.CharField(max_length=20, choices=PRIORIDAD_CHOICES, default=PRIORIDAD_MEDIA)
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_NUEVO)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    cliente = models.ForeignKey(
        'clients.Cliente',
        on_delete=models.RESTRICT,
        db_column='cliente_id'
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='pqrs_creados',
        db_column='creado_por_id'
    )
    ultima_respuesta_enviada = models.TextField(blank=True, null=True)
    correo_enviado = models.BooleanField(default=False)
    fecha_ultimo_correo = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.numero_caso} - {self.get_tipo_display()} de {self.cliente}'

    class Meta:
        managed = False
        db_table = 'pqrs'
        ordering = ['-fecha_creacion']


class PqrsEvento(models.Model):
    EVENTO_CREACION = 'creacion'
    EVENTO_ESTADO = 'estado'
    EVENTO_RESPUESTA = 'respuesta'
    EVENTO_NOTA = 'nota'

    TIPO_EVENTO_CHOICES = [
        (EVENTO_CREACION, 'Creación de PQRS'),
        (EVENTO_ESTADO, 'Cambio de Estado'),
        (EVENTO_RESPUESTA, 'Respuesta al Cliente'),
        (EVENTO_NOTA, 'Nota Interna'),
    ]

    pqrs = models.ForeignKey(
        Pqrs,
        related_name='eventos',
        on_delete=models.CASCADE,
        db_column='pqrs_id'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        db_column='usuario_id'
    )
    tipo_evento = models.CharField(max_length=20, choices=TIPO_EVENTO_CHOICES)
    comentario = models.TextField(blank=True, null=True)
    es_visible_cliente = models.BooleanField(default=True)
    enviado_por_correo = models.BooleanField(default=False)
    fecha_envio_correo = models.DateTimeField(null=True, blank=True)
    fecha_evento = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'Evento de {self.get_tipo_evento_display()} en {self.pqrs}'

    class Meta:
        managed = False
        db_table = 'pqrs_evento'
        ordering = ['-fecha_evento']


class PqrsAdjunto(models.Model):
    pqrs = models.ForeignKey(
        Pqrs,
        related_name='adjuntos',
        on_delete=models.CASCADE,
        db_column='pqrs_id'
    )
    nombre_archivo = models.CharField(max_length=255)
    ruta_archivo = models.CharField(max_length=500)
    tipo_mime = models.CharField(max_length=100)
    tamano_bytes = models.BigIntegerField()
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='subido_por_id'
    )
    fecha_subida = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.nombre_archivo} - {self.pqrs.numero_caso}'

    class Meta:
        managed = False
        db_table = 'pqrs_adjunto'
        ordering = ['-fecha_subida']