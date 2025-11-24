from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.db import transaction
from .models import Producto, Categoria, Lote, MovimientoInventario
from .forms import DescartarLoteForm

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'stock_actual', 'stock_minimo', 'precio_unitario', 'costo_promedio')
    list_filter = ('categoria',)
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)
    readonly_fields = ('stock_actual', 'costo_promedio')

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('numero_lote', 'producto', 'cantidad_disponible', 'costo_unitario_lote', 'fecha_caducidad', 'estado_lote')
    list_filter = ('producto__categoria', 'fecha_caducidad')
    search_fields = ('numero_lote', 'producto__nombre')
    autocomplete_fields = ['producto']
    actions = ['descartar_productos_action']
    
    def estado_lote(self, obj):
        """Muestra el estado del lote según su fecha de caducidad"""
        from datetime import date, timedelta
        
        if obj.cantidad_disponible == 0:
            return '🔴 Agotado'
        
        dias_restantes = (obj.fecha_caducidad - date.today()).days
        
        if dias_restantes < 0:
            return '⚠️ Vencido'
        elif dias_restantes <= 7:
            return f'🟡 Por vencer ({dias_restantes}d)'
        else:
            return f'🟢 Vigente ({dias_restantes}d)'
    
    estado_lote.short_description = 'Estado'
    
    def get_urls(self):
        """Agregar URL personalizada para descartar productos"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:lote_id>/descartar/',
                self.admin_site.admin_view(self.descartar_productos_view),
                name='inventory_lote_descartar',
            ),
        ]
        return custom_urls + urls
    
    @transaction.atomic
    def descartar_productos_view(self, request, lote_id):
        """Vista para descartar productos de un lote"""
        lote = Lote.objects.select_related('producto').get(pk=lote_id)
        
        if request.method == 'POST':
            form = DescartarLoteForm(request.POST, lote=lote)
            if form.is_valid():
                cantidad = form.cleaned_data['cantidad']
                motivo = form.cleaned_data['motivo']
                observaciones = form.cleaned_data['observaciones']
                
                # Actualizar cantidad disponible del lote
                lote.cantidad_disponible -= cantidad
                lote.save()
                
                # Registrar movimiento de inventario
                MovimientoInventario.objects.create(
                    producto=lote.producto,
                    lote=lote,
                    cantidad=-cantidad,  # Negativo porque es salida
                    tipo_movimiento='descarte',
                    descripcion=f'Descarte por {motivo} - Lote {lote.numero_lote}. {observaciones}'
                )
                
                messages.success(
                    request,
                    f'Se descartaron {cantidad} unidades de {lote.producto.nombre} (Lote: {lote.numero_lote}). '
                    f'Cantidad restante: {lote.cantidad_disponible}'
                )
                
                return redirect('admin:inventory_lote_changelist')
        else:
            form = DescartarLoteForm(lote=lote)
        
        context = {
            'form': form,
            'lote': lote,
            'title': f'Descartar productos del lote {lote.numero_lote}',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        
        return render(request, 'admin/inventory/descartar_lote.html', context)
    
    def descartar_productos_action(self, request, queryset):
        """Acción para descartar productos desde la lista"""
        if queryset.count() != 1:
            self.message_user(request, 'Seleccione solo un lote para descartar productos.', level=messages.WARNING)
            return
        
        lote = queryset.first()
        return redirect('admin:inventory_lote_descartar', lote_id=lote.id)
    
    descartar_productos_action.short_description = '🗑️ Descartar productos del lote seleccionado'

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('fecha_movimiento', 'tipo_movimiento', 'producto', 'lote', 'cantidad', 'descripcion_corta')
    list_filter = ('tipo_movimiento', 'fecha_movimiento', 'producto__categoria')
    search_fields = ('producto__nombre', 'lote__numero_lote', 'descripcion')
    readonly_fields = ('fecha_movimiento',)
    date_hierarchy = 'fecha_movimiento'
    
    def descripcion_corta(self, obj):
        """Muestra una versión corta de la descripción"""
        if obj.descripcion and len(obj.descripcion) > 50:
            return obj.descripcion[:50] + '...'
        return obj.descripcion or '-'
    
    descripcion_corta.short_description = 'Descripción'
    
    def has_add_permission(self, request):
        """No permitir agregar movimientos manualmente desde el admin"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar movimientos"""
        return False