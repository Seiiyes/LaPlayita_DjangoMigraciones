from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombres", "apellidos", "documento") 
    list_filter = ("nombres", "apellidos")
    search_fields = ("nombres", "apellidos", "documento", "correo")

# ---- MODELOS NO CREADOS EN DJANGO ----
from .models import PuntosFidelizacion, ProductoCanjeble, CanjeProducto

@admin.register(PuntosFidelizacion)
class PuntosFidelizacionAdmin(admin.ModelAdmin):
    list_display = ('cliente_id', 'tipo', 'puntos', 'descripcion', 'fecha_transaccion')
    list_filter = ('tipo', 'fecha_transaccion')
    search_fields = ('descripcion',)
    readonly_fields = ('fecha_transaccion',)

@admin.register(ProductoCanjeble)
class ProductoCanjebleAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'puntos_requeridos', 'stock_disponible', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('nombre',)
    readonly_fields = ('fecha_creacion',)

@admin.register(CanjeProducto)
class CanjeProductoAdmin(admin.ModelAdmin):
    list_display = ('cliente_id', 'producto_id', 'puntos_gastados', 'estado', 'fecha_canje')
    list_filter = ('estado', 'fecha_canje')
    search_fields = ('cliente_id',)
    readonly_fields = ('fecha_canje',)
