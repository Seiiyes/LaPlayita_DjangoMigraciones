import json
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.contrib import messages
from datetime import date, timedelta
from django.db import models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from .models import Producto, Lote, Categoria, MovimientoInventario
from .forms import ProductoForm, LoteForm, CategoriaForm
from users.decorators import check_user_role

# ----------------------------------------------
# Vistas de Gestión de Productos
# ----------------------------------------------

@never_cache
@login_required
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def inventario_list(request):
    productos = Producto.objects.select_related('categoria').order_by('nombre')

    form = ProductoForm()
    categoria_form = CategoriaForm()
    lote_form = LoteForm()

    context = {
        'productos': productos,
        'form': form,
        'categoria_form': categoria_form,
        'lote_form': lote_form,
        'alert_days_yellow': 60,
        'alert_days_red': 30,
    }
    return render(request, 'inventory/inventario_list.html', context)

@login_required
def producto_lotes_json(request, pk):
    print(f"Received pk for producto_lotes_json: {pk}") # Debugging line
    producto = get_object_or_404(Producto, pk=pk)

    # CORRECCIÓN DE ORM: La relación a proveedor no es directa.
    # El camino correcto es a través de reabastecimiento_detalle y reabastecimiento:
    lotes = Lote.objects.filter(producto=producto).order_by('-fecha_entrada')

    movimientos = MovimientoInventario.objects.filter(producto=producto).order_by('-fecha_movimiento')

    lotes_data = []
    for lote in lotes:
        # Lógica para obtener el nombre del proveedor de forma segura
        proveedor_nombre = 'N/A'
        if lote.reabastecimiento_detalle and \
           lote.reabastecimiento_detalle.reabastecimiento and \
           lote.reabastecimiento_detalle.reabastecimiento.proveedor:
            proveedor_nombre = lote.reabastecimiento_detalle.reabastecimiento.proveedor.nombre_empresa

        # Lógica de fechas segura (para evitar fallos de strftime en None)
        fecha_caducidad_str = 'N/A'
        if lote.fecha_caducidad:
             try:
                 fecha_caducidad_str = lote.fecha_caducidad.strftime('%Y-%m-%d')
             except AttributeError:
                 fecha_caducidad_str = lote.fecha_caducidad.isoformat()

        fecha_entrada_str = 'N/A'
        if lote.fecha_entrada:
             fecha_entrada_str = timezone.localtime(lote.fecha_entrada).strftime('%d/%m/%Y %H:%M')

        lotes_data.append({
            'id': lote.id,
            'numero_lote': lote.numero_lote,
            'cantidad_disponible': lote.cantidad_disponible,
            # Asegura un valor float válido (0.0) si es None
            'costo_unitario_lote': float(lote.costo_unitario_lote) if lote.costo_unitario_lote is not None else 0.0,
            'fecha_caducidad': fecha_caducidad_str,
            'fecha_entrada': fecha_entrada_str,
            'proveedor': proveedor_nombre, # Se usa el nombre de proveedor seguro
        })

    movimientos_data = [{
        # Asegura que la fecha de movimiento no sea nula antes de formatear
        'fecha_movimiento': timezone.localtime(m.fecha_movimiento).strftime('%d/%m/%Y %H:%M') if m.fecha_movimiento else 'N/A',
        'tipo_movimiento': m.tipo_movimiento,
        'cantidad': m.cantidad,
        'descripcion': m.descripcion or '', # Asegura una cadena vacía si es NULL
    } for m in movimientos]

    # Lógica para el último proveedor (también debe usar el camino correcto)
    ultimo_proveedor = 'N/A'
    if lotes.exists():
        primer_lote = lotes.first()
        if primer_lote.reabastecimiento_detalle and primer_lote.reabastecimiento_detalle.reabastecimiento and primer_lote.reabastecimiento_detalle.reabastecimiento.proveedor:
            ultimo_proveedor = primer_lote.reabastecimiento_detalle.reabastecimiento.proveedor.nombre_empresa

    data = {
        'id': producto.pk,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion or '', # Asegura una cadena vacía si es NULL
        # Asegura un float válido para precio_unitario si es None
        'precio_unitario': float(producto.precio_unitario) if producto.precio_unitario is not None else 0.0,
        'stock_actual': producto.stock_actual,
        'stock_minimo': producto.stock_minimo,
        # Maneja la relación Categoria si por alguna razón fuera None
        'categoria': producto.categoria.nombre if producto.categoria else 'N/A',
        'lotes': lotes_data,
        'movimientos': movimientos_data,
        'ultimo_proveedor': ultimo_proveedor,
        'costo_promedio': float(producto.costo_promedio) if producto.costo_promedio is not None else 0.0,
    }
    return JsonResponse(data)

@login_required
def lote_create_form_ajax(request, producto_pk):
    producto = get_object_or_404(Producto, pk=producto_pk)
    form = LoteForm(initial={'producto': producto})
    return render(request, 'inventory/_lote_form.html', {'form': form, 'producto': producto})


@never_cache
@login_required
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def alertas_stock_list(request):
    productos = Producto.objects.filter(stock_actual__lt=models.F('stock_minimo')).select_related('categoria')
    form = ProductoForm()
    context = {
        'productos': productos,
        'form': form,
        'alertas_stock': True,
    }
    return render(request, 'inventory/inventario_list.html', context)

@never_cache
@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def producto_create(request):
    form = ProductoForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Producto creado exitosamente.')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"Error en {form.fields[field].label}: {error}")
    return redirect('inventory:inventario_list')

@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def producto_create_ajax(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'errors': 'JSON inválido'}, status=400)

    form = ProductoForm(data)
    if form.is_valid():
        producto = form.save()
        return JsonResponse({
            'id': producto.pk,
            'nombre': producto.nombre,
            'categoria_nombre': producto.categoria.nombre if producto.categoria else 'N/A',
            'precio_unitario': str(producto.precio_unitario or 0),
            'stock_actual': producto.stock_actual,
            'stock_minimo': producto.stock_minimo,
        })
    else:
        return JsonResponse({'errors': form.errors}, status=400)

@login_required
def producto_detail_json(request, pk):
    """
    Devuelve los detalles de un producto en formato JSON para la edición en modal.
    (Aplicamos correcciones de nulabilidad aquí también para consistencia)
    """
    producto = get_object_or_404(Producto, pk=pk)
    data = {
        'id': producto.pk,
        'nombre': producto.nombre,
        # Corrección: Asegura que sea una cadena '0' o el valor si es None
        'precio_unitario': str(producto.precio_unitario) if producto.precio_unitario is not None else '0',
        'descripcion': producto.descripcion or '', # Corrección: Asegura una cadena vacía
        'stock_minimo': producto.stock_minimo,
        'categoria_id': producto.categoria_id,
    }
    return JsonResponse(data)

@never_cache
@login_required
@require_POST # This view now only handles POST requests
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def producto_update(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST, instance=producto)
    if form.is_valid():
        producto = form.save()
        return JsonResponse({
            'id': producto.pk,
            'nombre': producto.nombre,
            'categoria_nombre': producto.categoria.nombre if producto.categoria else 'N/A', # Corrección: Manejo de categoria nula
            'precio_unitario': str(producto.precio_unitario or 0),
            'stock_actual': producto.stock_actual,
            'stock_minimo': producto.stock_minimo,
        })
    else:
        return JsonResponse({'errors': form.errors}, status=400)

@never_cache
@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador'])
def producto_delete(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.delete()
    messages.success(request, 'Producto eliminado exitosamente.')
    return redirect('inventory:inventario_list')

@never_cache
@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def categoria_create(request):
    if 'application/json' in request.headers.get('Content-Type', ''):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido.'}, status=400)
        
        form = CategoriaForm(data)
        if form.is_valid():
            categoria = form.save()
            return JsonResponse({'id': categoria.pk, 'nombre': categoria.nombre}, status=201)
        else:
            return JsonResponse({'errors': form.errors}, status=400)

    # Fallback para el comportamiento no-AJAX si aún es necesario
    form = CategoriaForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Categoría creada exitosamente.')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"Error en {form.fields[field].label}: {error}")
    return redirect('inventory:inventario_list')

# ----------------------------------------------
# Vistas de Gestión de Lotes (Trazabilidad)
# ----------------------------------------------

@never_cache
@login_required
@check_user_role(allowed_roles=['Administrador'])
def lote_list(request, producto_pk):
    producto = get_object_or_404(Producto, pk=producto_pk)
    lotes = Lote.objects.filter(producto=producto).order_by('-fecha_entrada')
    form = LoteForm(initial={'producto': producto})
    
    today = date.today()
    thirty_days_from_now = today + timedelta(days=30)

    context = {
        'lotes': lotes,
        'producto': producto,
        'form': form,
        'today': today,
        'thirty_days_from_now': thirty_days_from_now,
    }
    return render(request, 'inventory/lote_list.html', context)