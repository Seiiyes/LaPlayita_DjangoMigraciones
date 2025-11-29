from django.shortcuts import render, get_object_or_404
from decimal import Decimal
import json
from django.db import transaction
from django.db.models import Sum, F, Count, Avg
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from weasyprint import HTML
from inventory.models import Producto, Lote, MovimientoInventario
from clients.models import Cliente, PuntosFidelizacion
from .models import Venta, VentaDetalle, Pago
from .forms import ProductoSearchForm, VentaForm
from users.decorators import check_user_role
from django.core.mail import EmailMessage
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models.functions import TruncDate

# Constante: 5.5 puntos por cada $66,000 pesos
PUNTOS_POR_COMPRA = Decimal('5.5')
VALOR_BASE_PUNTOS = Decimal('66000')
# VALOR_PUNTO = Decimal('15000.00')

@login_required
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def pos_view(request):
    productos = Producto.objects.filter(stock_actual__gt=0).select_related('categoria').order_by('nombre')
    search_form = ProductoSearchForm()
    venta_form = VentaForm()
    context = {
        'productos': productos,
        'search_form': search_form,
        'venta_form': venta_form,
    }
    return render(request, 'pos/pos_main.html', context)

@login_required
def listar_ventas(request):
    ventas = Venta.objects.select_related('cliente', 'usuario').order_by('-fecha_venta')

    fecha = request.GET.get('fecha')
    if fecha:
        try:
            fecha_dt = datetime.strptime(fecha, '%Y-%m-%d').date()
            ventas = ventas.filter(fecha_venta__date=fecha_dt)
        except Exception:
            pass

    metodo_pago = request.GET.get('metodo_pago')
    if metodo_pago:
        ventas = ventas.filter(pago__metodo_pago=metodo_pago)

    return render(request, 'pos/listar_ventas.html', {'ventas': ventas})

@login_required
def buscar_productos(request):
    query = request.GET.get('q', '')
    productos = Producto.objects.filter(nombre__icontains=query, stock_actual__gt=0).select_related('categoria')
    productos_data = [{
        'id': p.id,
        'nombre': p.nombre,
        'precio': p.precio_unitario,
        'stock': p.stock_actual,
        'categoria': p.categoria.nombre if p.categoria else 'Sin categoría',
        'descripcion': p.descripcion or ''
    } for p in productos]
    return JsonResponse({'productos': productos_data})

@login_required
def obtener_producto(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    lotes = Lote.objects.filter(producto=producto, cantidad_disponible__gt=0).order_by('fecha_caducidad')

    # Comprobar y corregir inconsistencia de stock
    if producto.stock_actual > 0 and not lotes.exists():
        producto.actualizar_costo_promedio_y_stock()
        # Refrescar el objeto producto y los lotes
        producto.refresh_from_db()
        lotes = Lote.objects.filter(producto=producto, cantidad_disponible__gt=0).order_by('fecha_caducidad')

    producto_data = {
        'id': producto.id,
        'nombre': producto.nombre,
        'precio': producto.precio_unitario,
        'stock': producto.stock_actual,
        'categoria': producto.categoria.nombre if producto.categoria else 'Sin categoría',
        'descripcion': producto.descripcion or '',
        'lotes': [{
            'id': lote.id,
            'numero_lote': lote.numero_lote,
            'cantidad': lote.cantidad_disponible,
            'fecha_caducidad': lote.fecha_caducidad.strftime('%Y-%m-%d') if lote.fecha_caducidad else 'N/A'
        } for lote in lotes]
    }
    return JsonResponse(producto_data)

@login_required
@require_POST
@transaction.atomic
def procesar_venta(request):
    try:
        data = json.loads(request.body)
        cart_items = data.get('items', [])
        
        if not cart_items:
            return JsonResponse({'success': False, 'error': 'El carrito está vacío.'}, status=400)
        
        cliente_id = data.get('cliente_id')
        cliente = get_object_or_404(Cliente, pk=cliente_id) if cliente_id else get_object_or_404(Cliente, pk=1)
        
        total_venta = sum(Decimal(item['precio']) * int(item['cantidad']) for item in cart_items)
        
        nueva_venta = Venta.objects.create(
            cliente=cliente,
            usuario=request.user,
            canal_venta=data['canal_venta'],
            total_venta=total_venta
        )
        
        Pago.objects.create(
            venta=nueva_venta,
            monto=total_venta,
            metodo_pago=data['metodo_pago'],
            estado='completado'
        )
        
        productos_a_actualizar = set()
        for item in cart_items:
            producto = get_object_or_404(Producto, pk=item['producto_id'])
            lote = get_object_or_404(Lote, pk=item['lote_id'])
            cantidad = int(item['cantidad'])
            
            if lote.cantidad_disponible < cantidad:
                raise Exception(f"No hay suficiente stock de '{producto.nombre}'. Solicitado: {cantidad}, Disponible: {lote.cantidad_disponible} (Lote: {lote.numero_lote})")
            
            VentaDetalle.objects.create(
                venta=nueva_venta,
                producto=producto,
                lote=lote,
                cantidad=cantidad,
                subtotal=Decimal(item['precio']) * cantidad
            )
            
            # Actualizar cantidad disponible del lote
            lote.cantidad_disponible -= cantidad
            lote.save()
            
            # ===== REGISTRAR MOVIMIENTO DE INVENTARIO =====
            MovimientoInventario.objects.create(
                producto=producto,
                lote=lote,
                cantidad=-cantidad,  # Negativo porque es una salida
                tipo_movimiento='salida',
                descripcion=f'Venta #{nueva_venta.id} - {producto.nombre}',
                venta=nueva_venta
            )
            
            productos_a_actualizar.add(producto)

        for producto in productos_a_actualizar:
            # producto.actualizar_costo_promedio_y_stock()  # Comentado: los triggers de BD ya actualizan esto
            pass  # Los triggers de MySQL manejan la actualización automáticamente
        
        # ===== AGREGAR PUNTOS AL CLIENTE =====
        puntos_ganados = Decimal('0')
        if cliente.id != 1:  # No agregar puntos a "Consumidor Final"
            # Calcular puntos: (total_venta / 66000) * 5.5
            puntos_ganados = ((total_venta / VALOR_BASE_PUNTOS) * PUNTOS_POR_COMPRA).quantize(Decimal('0.01'))
            
            # Actualizar puntos del cliente
            cliente.puntos_totales += puntos_ganados
            cliente.save()
            
            # Registrar transacción de puntos
            PuntosFidelizacion.objects.create(
                cliente=cliente,
                tipo=PuntosFidelizacion.TIPO_GANANCIA,
                puntos=puntos_ganados,
                descripcion=f'Compra de ${total_venta} - Venta #{nueva_venta.id}',
                venta_id=nueva_venta.id
            )
        
        return JsonResponse({
            'success': True,
            'venta_id': nueva_venta.id,
            'puntos_ganados': float(puntos_ganados) if cliente.id != 1 else 0,
            'mensaje': f'Venta #{nueva_venta.id} procesada con éxito.'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def venta_detalle(request, venta_id):
    venta = get_object_or_404(Venta.objects.select_related('cliente', 'usuario'), pk=venta_id)
    detalles = VentaDetalle.objects.filter(venta=venta).select_related('producto', 'lote')
    pago = Pago.objects.filter(venta=venta).first()
    impuesto = float(venta.total_venta) * 0.19
    return render(request, 'pos/venta_detalle.html', {
        'venta': venta,
        'detalles': detalles,
        'pago': pago,
        'impuesto': impuesto
    })

@login_required
def obtener_clientes(request):
    try:
        clientes = list(Cliente.objects.all().values('id', 'nombres', 'apellidos').order_by('nombres'))
        clientes_formateados = []
        for c in clientes:
            nombre_completo = f"{c['nombres']} {c['apellidos']}".strip()
            clientes_formateados.append({
                'id': c['id'],
                'nombre': nombre_completo
            })
        return JsonResponse({
            'success': True,
            'clientes': clientes_formateados,
            'total': len(clientes_formateados)
        })
    except Exception as e:
        import traceback
        print(f"[ERROR OBTENER_CLIENTES] {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'clientes': []
        }, status=500)

@login_required
def descargar_factura(request, venta_id):
    venta = get_object_or_404(Venta.objects.select_related('cliente', 'usuario'), pk=venta_id)
    detalles = VentaDetalle.objects.filter(venta=venta).select_related('producto', 'lote')
    pago = Pago.objects.filter(venta=venta).first()
    impuesto = float(venta.total_venta) * 0.19
    html_string = render_to_string('pos/factura.html', {
        'venta': venta,
        'detalles': detalles,
        'pago': pago,
        'impuesto': impuesto
    })
    pdf = HTML(string=html_string).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura_venta_{venta.id}.pdf"'
    return response

@login_required
def enviar_factura(request, venta_id):
    venta = get_object_or_404(Venta.objects.select_related('cliente', 'usuario'), pk=venta_id)
    if venta.cliente.nombres == "Consumidor" and venta.cliente.apellidos == "Final":
        return JsonResponse({'success': False, 'error': 'No se puede enviar factura por correo a Consumidor Final.'}, status=400)
    detalles = VentaDetalle.objects.filter(venta=venta).select_related('producto', 'lote')
    pago = Pago.objects.filter(venta=venta).first()
    impuesto = float(venta.total_venta) * 0.19
    html_string = render_to_string('pos/factura.html', {
        'venta': venta,
        'detalles': detalles,
        'pago': pago,
        'impuesto': impuesto
    })
    pdf_file = HTML(string=html_string).write_pdf()
    destinatario = venta.cliente.correo
    asunto = f"Factura de venta #{venta.id} - La Playita"
    cuerpo = f"""
        Estimado/a {venta.cliente.nombres} {venta.cliente.apellidos},
        Adjunto encontrará la factura generada para su compra en La Playita.
        ¡Gracias por su preferencia!
    """
    email = EmailMessage(
        subject=asunto,
        body=cuerpo,
        from_email=None,
        to=[destinatario]
    )
    email.attach(filename=f"factura_venta_{venta.id}.pdf", content=pdf_file, mimetype="application/pdf")
    try:
        email.send()
        return JsonResponse({'success': True, 'mensaje': 'Factura enviada correctamente.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
def crear_cliente(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            cliente = Cliente.objects.create(
                documento=data['documento'],
                nombres=data['nombres'],
                apellidos=data['apellidos'],
                correo=data['correo'],
                telefono=data['telefono']
            )
            return JsonResponse({'success': True, 'cliente_id': cliente.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


# ==================== DASHBOARD DE REPORTES ====================

@login_required
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def dashboard_reportes(request):
    """Dashboard principal con métricas y KPIs de ventas"""
    from django.db.models import F
    
    ahora = timezone.now()
    hoy_inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    hace_7_dias = ahora - timedelta(days=7)
    hace_30_dias = ahora - timedelta(days=30)
    
    # Datos de inventario para accesos rápidos
    total_productos = Producto.objects.count()
    productos_bajos_stock = Producto.objects.filter(stock_actual__lt=F('stock_minimo')).count()
    productos_agotados = Producto.objects.filter(stock_actual=0).count()
    
    # Valor total del inventario
    from django.db.models import Sum as DbSum
    valor_inventario = Producto.objects.aggregate(
        total=DbSum(F('stock_actual') * F('costo_promedio'))
    )['total'] or Decimal('0')
    
    # Calcular margen de ganancia (últimos 30 días)
    ventas_con_costo = VentaDetalle.objects.filter(
        venta__fecha_venta__gte=hace_30_dias
    ).aggregate(
        ingresos=Sum('subtotal'),
        costos=Sum(F('cantidad') * F('lote__costo_unitario_lote'))
    )
    
    ingresos_30dias = ventas_con_costo['ingresos'] or Decimal('0')
    costos_30dias = ventas_con_costo['costos'] or Decimal('0')
    ganancia_bruta = ingresos_30dias - costos_30dias
    margen_porcentaje = (ganancia_bruta / ingresos_30dias * 100) if ingresos_30dias > 0 else Decimal('0')
    
    # Productos con bajo movimiento (últimos 30 días)
    productos_vendidos = VentaDetalle.objects.filter(
        venta__fecha_venta__gte=hace_30_dias
    ).values('producto_id').distinct()
    
    productos_sin_movimiento = Producto.objects.exclude(
        id__in=productos_vendidos
    ).filter(stock_actual__gt=0).count()
    
    # Ventas del día
    ventas_hoy = Venta.objects.filter(fecha_venta__gte=hoy_inicio)
    total_hoy = ventas_hoy.aggregate(Sum('total_venta'))['total_venta__sum'] or Decimal('0')
    cantidad_hoy = ventas_hoy.count()
    
    # Ventas últimos 7 días
    ventas_7dias = Venta.objects.filter(fecha_venta__gte=hace_7_dias)
    total_7dias = ventas_7dias.aggregate(Sum('total_venta'))['total_venta__sum'] or Decimal('0')
    cantidad_7dias = ventas_7dias.count()
    
    # Ventas últimos 30 días
    ventas_30dias = Venta.objects.filter(fecha_venta__gte=hace_30_dias)
    total_30dias = ventas_30dias.aggregate(Sum('total_venta'))['total_venta__sum'] or Decimal('0')
    cantidad_30dias = ventas_30dias.count()
    
    # Ticket promedio
    ticket_promedio = total_30dias / cantidad_30dias if cantidad_30dias > 0 else Decimal('0')
    
    # Métodos de pago (últimos 30 días)
    metodos_pago = Pago.objects.filter(
        venta__fecha_venta__gte=hace_30_dias
    ).values('metodo_pago').annotate(
        total=Sum('monto'),
        cantidad=Count('id')
    ).order_by('-total')
    
    # Canales de venta (últimos 30 días)
    canales_venta = Venta.objects.filter(
        fecha_venta__gte=hace_30_dias
    ).values('canal_venta').annotate(
        total=Sum('total_venta'),
        cantidad=Count('id')
    ).order_by('-total')
    
    # Top 5 productos más vendidos (últimos 30 días)
    top_productos = VentaDetalle.objects.filter(
        venta__fecha_venta__gte=hace_30_dias
    ).values('producto__nombre').annotate(
        cantidad_total=Sum('cantidad'),
        ingresos=Sum('subtotal')
    ).order_by('-cantidad_total')[:5]
    
    # Top 5 vendedores (últimos 30 días)
    top_vendedores = Venta.objects.filter(
        fecha_venta__gte=hace_30_dias
    ).values(
        'usuario__first_name', 
        'usuario__last_name',
        'usuario__username'
    ).annotate(
        total_ventas=Sum('total_venta'),
        cantidad=Count('id')
    ).order_by('-total_ventas')[:5]
    
    # Top 5 clientes (últimos 30 días)
    top_clientes = Venta.objects.filter(
        fecha_venta__gte=hace_30_dias
    ).exclude(
        cliente__nombres='Consumidor',
        cliente__apellidos='Final'
    ).values(
        'cliente__nombres',
        'cliente__apellidos'
    ).annotate(
        total_compras=Sum('total_venta'),
        cantidad=Count('id')
    ).order_by('-total_compras')[:5]
    
    # Estadísticas adicionales
    total_clientes = Cliente.objects.exclude(
        nombres='Consumidor',
        apellidos='Final'
    ).count()
    
    # Comparativa con período anterior (30 días vs 60 días)
    hace_60_dias = ahora - timedelta(days=60)
    ventas_periodo_anterior = Venta.objects.filter(
        fecha_venta__gte=hace_60_dias,
        fecha_venta__lt=hace_30_dias
    )
    total_periodo_anterior = ventas_periodo_anterior.aggregate(Sum('total_venta'))['total_venta__sum'] or Decimal('0')
    
    # Calcular crecimiento
    if total_periodo_anterior > 0:
        crecimiento = ((total_30dias - total_periodo_anterior) / total_periodo_anterior * 100)
    else:
        crecimiento = 100 if total_30dias > 0 else 0
    
    # Producto más vendido del día
    producto_dia = VentaDetalle.objects.filter(
        venta__fecha_venta__gte=hoy_inicio
    ).values('producto__nombre').annotate(
        cantidad_total=Sum('cantidad')
    ).order_by('-cantidad_total').first()
    
    # Hora pico de ventas (últimos 7 días)
    ventas_por_hora_analisis = {}
    for venta in Venta.objects.filter(fecha_venta__gte=hace_7_dias):
        hora = venta.fecha_venta.hour
        ventas_por_hora_analisis[hora] = ventas_por_hora_analisis.get(hora, 0) + 1
    
    hora_pico = max(ventas_por_hora_analisis.items(), key=lambda x: x[1])[0] if ventas_por_hora_analisis else 0
    
    context = {
        'total_hoy': float(total_hoy),
        'cantidad_hoy': cantidad_hoy,
        'total_7dias': float(total_7dias),
        'cantidad_7dias': cantidad_7dias,
        'total_30dias': float(total_30dias),
        'cantidad_30dias': cantidad_30dias,
        'ticket_promedio': float(ticket_promedio),
        'metodos_pago': list(metodos_pago),
        'canales_venta': list(canales_venta),
        'top_productos': list(top_productos),
        'top_vendedores': list(top_vendedores),
        'top_clientes': list(top_clientes),
        'total_productos': total_productos,
        'productos_bajos_stock': productos_bajos_stock,
        'productos_agotados': productos_agotados,
        'valor_inventario': float(valor_inventario),
        'total_clientes': total_clientes,
        'crecimiento': float(crecimiento),
        'producto_dia': producto_dia,
        'hora_pico': hora_pico,
        'ganancia_bruta': float(ganancia_bruta),
        'margen_porcentaje': float(margen_porcentaje),
        'productos_sin_movimiento': productos_sin_movimiento,
        'ingresos_30dias': float(ingresos_30dias),
        'costos_30dias': float(costos_30dias),
    }
    
    return render(request, 'pos/dashboard_reportes.html', context)


@login_required
def api_ventas_por_fecha(request):
    """API para gráfico de ventas por fecha (últimos 30 días)"""
    dias = int(request.GET.get('dias', 30))
    fecha_inicio = timezone.now() - timedelta(days=dias)
    
    ventas_por_fecha = Venta.objects.filter(
        fecha_venta__gte=fecha_inicio
    ).annotate(
        fecha=TruncDate('fecha_venta')
    ).values('fecha').annotate(
        total=Sum('total_venta'),
        cantidad=Count('id')
    ).order_by('fecha')
    
    datos = {
        'fechas': [v['fecha'].strftime('%Y-%m-%d') for v in ventas_por_fecha],
        'totales': [float(v['total']) for v in ventas_por_fecha],
        'cantidades': [v['cantidad'] for v in ventas_por_fecha],
    }
    
    return JsonResponse(datos)


@login_required
def api_comparativa_metodos_pago(request):
    """API para comparativa de métodos de pago"""
    dias = int(request.GET.get('dias', 30))
    fecha_inicio = timezone.now() - timedelta(days=dias)
    
    datos = Pago.objects.filter(
        venta__fecha_venta__gte=fecha_inicio
    ).values('metodo_pago').annotate(
        total=Sum('monto'),
        cantidad=Count('id')
    ).order_by('-total')
    
    return JsonResponse({
        'metodos': [d['metodo_pago'] for d in datos],
        'totales': [float(d['total']) for d in datos],
        'cantidades': [d['cantidad'] for d in datos],
    })


@login_required
def api_ventas_por_hora(request):
    """API para análisis de ventas por hora del día"""
    dias = int(request.GET.get('dias', 7))
    fecha_inicio = timezone.now() - timedelta(days=dias)
    
    ventas = Venta.objects.filter(fecha_venta__gte=fecha_inicio)
    
    # Agrupar por hora
    ventas_por_hora = {}
    for venta in ventas:
        hora = venta.fecha_venta.hour
        if hora not in ventas_por_hora:
            ventas_por_hora[hora] = {'cantidad': 0, 'total': 0}
        ventas_por_hora[hora]['cantidad'] += 1
        ventas_por_hora[hora]['total'] += float(venta.total_venta)
    
    # Ordenar por hora
    horas = sorted(ventas_por_hora.keys())
    
    return JsonResponse({
        'horas': [f"{h:02d}:00" for h in horas],
        'cantidades': [ventas_por_hora[h]['cantidad'] for h in horas],
        'totales': [ventas_por_hora[h]['total'] for h in horas],
    })
