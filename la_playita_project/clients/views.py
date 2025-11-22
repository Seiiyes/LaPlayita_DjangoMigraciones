from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from users.decorators import check_user_role
from .models import Cliente, PuntosFidelizacion, ProductoCanjeble, CanjeProducto
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.urls import reverse
from django.contrib import messages
from decimal import Decimal
import json

# ==================== ADMIN & CLIENTE CRUD ====================

@login_required
@check_user_role(allowed_roles=['Administrador'])
def cliente_list(request):
    clientes = Cliente.objects.all().order_by('nombres')
    return render(request, 'clients/cliente_list.html', {'clientes': clientes})

@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def cliente_create_ajax(request):
    try:
        data = json.loads(request.body)
        if Cliente.objects.filter(documento=data.get('documento')).exists():
            return JsonResponse({'error': 'Ya existe un cliente con este documento.'}, status=400)
        cliente = Cliente.objects.create(
            nombres=data.get('nombres'),
            apellidos=data.get('apellidos'),
            documento=data.get('documento'),
            telefono=data.get('telefono'),
            correo=data.get('email'),
        )
        return JsonResponse({
            'id': cliente.id,
            'nombres': cliente.nombres,
            'apellidos': cliente.apellidos,
            'documento': cliente.documento,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# ==================== PANEL Y PUNTOS ====================

@login_required
def panel_puntos(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    transacciones = PuntosFidelizacion.objects.filter(cliente_id=cliente_id).order_by('-fecha_transaccion')[:20]
    productos = ProductoCanjeble.objects.filter(activo=True, stock_disponible__gt=0).order_by('puntos_requeridos')
    context = {
        'cliente': cliente,
        'transacciones': transacciones,
        'puntos_totales': cliente.puntos_totales,
        'productos': productos,  # Para mostrar catálogo y botón de canje
    }
    return render(request, 'clients/panel_puntos.html', context)

@login_required
def historial_puntos(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    transacciones = PuntosFidelizacion.objects.filter(cliente_id=cliente_id).order_by('-fecha_transaccion')
    context = {
        'cliente': cliente,
        'transacciones': transacciones,
    }
    return render(request, 'clients/historial_puntos.html', context)

@login_required
def mi_panel_puntos(request):
    cliente = Cliente.objects.filter(correo=request.user.email).first()
    if not cliente:
        return render(request, 'clients/sin_cliente.html', {
            'mensaje': 'No tienes perfil de cliente asociado'
        })
    transacciones = PuntosFidelizacion.objects.filter(cliente_id=cliente.id).order_by('-fecha_transaccion')[:10]
    canjes = CanjeProducto.objects.filter(cliente_id=cliente.id).order_by('-fecha_canje')[:5]
    productos = ProductoCanjeble.objects.filter(activo=True, stock_disponible__gt=0).order_by('puntos_requeridos')
    context = {
        'cliente': cliente,
        'transacciones': transacciones,
        'canjes': canjes,
        'productos': productos,
        'puntos_totales': cliente.puntos_totales,
    }
    return render(request, 'clients/mi_panel_puntos.html', context)

# ==================== CATÁLOGO DE PRODUCTOS ====================

@login_required
def productos_canjebles(request):
    productos = ProductoCanjeble.objects.filter(activo=True, stock_disponible__gt=0).order_by('puntos_requeridos')
    try:
        cliente = Cliente.objects.get(correo=request.user.email)
    except Cliente.DoesNotExist:
        cliente = None
    context = {
        'productos': productos,
        'cliente': cliente,
    }
    return render(request, 'clients/productos_canjebles.html', context)

# ==================== CANJEAR PRODUCTO: AJAX ====================

@login_required
@require_POST
def canjear_producto(request, producto_id):
    try:
        data = json.loads(request.body)
        cliente_id = data.get('cliente_id')
        cliente = get_object_or_404(Cliente, pk=cliente_id)
        producto = get_object_or_404(ProductoCanjeble, pk=producto_id)
        if producto.stock_disponible <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Producto sin stock disponible'
            }, status=400)
        if cliente.puntos_totales < producto.puntos_requeridos:
            return JsonResponse({
                'success': False,
                'error': f'Puntos insuficientes. Requiere {producto.puntos_requeridos} pts, tienes {cliente.puntos_totales} pts'
            }, status=400)
        with transaction.atomic():
            canje = CanjeProducto.objects.create(
                cliente_id=cliente.id,
                producto_id=producto.id,
                puntos_gastados=producto.puntos_requeridos,
                estado=CanjeProducto.ESTADO_PENDIENTE
            )
            cliente.puntos_totales -= producto.puntos_requeridos
            cliente.save()
            producto.stock_disponible -= 1
            producto.save()
            PuntosFidelizacion.objects.create(
                cliente_id=cliente.id,
                tipo=PuntosFidelizacion.TIPO_CANJE,
                puntos=-producto.puntos_requeridos,
                descripcion=f'Canje de {producto.nombre} (Canje #{canje.id})',
                canje_id=canje.id
            )
        return JsonResponse({
            'success': True,
            'mensaje': f'Canje realizado exitosamente. Canje #{canje.id}',
            'canje_id': canje.id,
            'puntos_restantes': float(cliente.puntos_totales)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== CANJE TRADICIONAL (HTML CON CONFIRMACIÓN) ====================

@login_required
@require_http_methods(["GET", "POST"])
@transaction.atomic
def canjearproducto_web(request, producto_id):
    producto = get_object_or_404(ProductoCanjeble, pk=producto_id)
    cliente = Cliente.objects.get(correo=request.user.email)
    if cliente.id == 1:
        messages.error(request, "Los consumidores finales no pueden canjear puntos.")
        return redirect('clients:mi_panel_puntos')
    if request.method == "GET":
        puntos_disponibles = cliente.puntos_totales
        puntos_requeridos = producto.puntos_requeridos
        puede_canjear = puntos_disponibles >= puntos_requeridos
        context = {
            'producto': producto,
            'cliente': cliente,
            'puntos_disponibles': puntos_disponibles,
            'puntos_requeridos': puntos_requeridos,
            'puede_canjear': puede_canjear,
            'diferencia': puntos_requeridos - puntos_disponibles if not puede_canjear else 0
        }
        return render(request, 'clients/confirmar_canje.html', context)
    elif request.method == "POST":
        puntos_disponibles = cliente.puntos_totales
        puntos_requeridos = producto.puntos_requeridos
        if puntos_disponibles < puntos_requeridos:
            messages.error(request, f'Necesitas {puntos_requeridos} pts y tienes {puntos_disponibles}.')
            return redirect(request.path)
        if producto.stock_disponible <= 0:
            messages.error(request, 'Producto sin stock.')
            return redirect(request.path)
        try:
            cliente.puntos_totales -= puntos_requeridos
            cliente.save()
            producto.stock_disponible -= 1
            producto.save()
            canje = CanjeProducto.objects.create(
                cliente=cliente,
                producto=producto,
                puntos_gastados=puntos_requeridos,
                estado=CanjeProducto.ESTADO_COMPLETADO
            )
            PuntosFidelizacion.objects.create(
                cliente=cliente,
                tipo=PuntosFidelizacion.TIPO_CANJE,
                puntos=-puntos_requeridos,
                descripcion=f'Canje de {producto.nombre} (Web)',
                canje=canje
            )
            messages.success(request, f'¡Canje realizado correctamente!')
            return redirect('clients:canjes_cliente', cliente_id=cliente.id)
        except Exception as e:
            messages.error(request, f'Error en el canje: {str(e)}')
            return redirect(request.path)

# ==================== HISTORIAL DE CANJES ====================

@login_required
def canjes_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    canjes = CanjeProducto.objects.filter(cliente_id=cliente_id).order_by('-fecha_canje')
    context = {
        'cliente': cliente,
        'canjes': canjes,
    }
    return render(request, 'clients/canjes_cliente.html', context)

# ==================== ADMINISTRACIÓN PRODUCTOS CANJEBLES ====================

@login_required
@check_user_role(allowed_roles=['Administrador'])
def administrar_productos_canjebles(request):
    productos = ProductoCanjeble.objects.all().order_by('-fecha_creacion')
    return render(request, 'clients/admin_productos_canjebles.html', {'productos': productos})

@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador'])
def crear_producto_canjeble(request):
    try:
        data = json.loads(request.body)
        producto = ProductoCanjeble.objects.create(
            nombre=data.get('nombre'),
            descripcion=data.get('descripcion', ''),
            puntos_requeridos=Decimal(data.get('puntos_requeridos', 0)),
            stock_disponible=int(data.get('stock_disponible', 0)),
            activo=data.get('activo', True)
        )
        return JsonResponse({
            'success': True,
            'id': producto.id,
            'nombre': producto.nombre,
            'puntos_requeridos': float(producto.puntos_requeridos),
            'stock_disponible': producto.stock_disponible,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador'])
def editar_producto_canjeble(request, producto_id):
    try:
        data = json.loads(request.body)
        producto = get_object_or_404(ProductoCanjeble, pk=producto_id)
        producto.nombre = data.get('nombre', producto.nombre)
        producto.descripcion = data.get('descripcion', producto.descripcion)
        producto.puntos_requeridos = Decimal(data.get('puntos_requeridos', producto.puntos_requeridos))
        producto.stock_disponible = int(data.get('stock_disponible', producto.stock_disponible))
        producto.activo = data.get('activo', producto.activo)
        producto.save()
        return JsonResponse({'success': True, 'mensaje': 'Producto actualizado correctamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador'])
def eliminar_producto_canjeble(request, producto_id):
    try:
        producto = get_object_or_404(ProductoCanjeble, pk=producto_id)
        producto_nombre = producto.nombre
        producto.delete()
        return JsonResponse({'success': True, 'mensaje': f'Producto \"{producto_nombre}\" eliminado correctamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador'])
def marcar_canje_entregado(request, canje_id):
    try:
        canje = get_object_or_404(CanjeProducto, pk=canje_id)
        canje.estado = CanjeProducto.ESTADO_COMPLETADO
        canje.fecha_entrega = timezone.now()
        canje.save()
        return JsonResponse({'success': True, 'mensaje': f'Canje #{canje_id} marcado como entregado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
