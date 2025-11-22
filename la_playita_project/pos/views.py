from django.shortcuts import render, get_object_or_404
from decimal import Decimal
import json
from django.db import transaction
from django.db.models import Sum, F
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from weasyprint import HTML
from inventory.models import Producto, Lote
from clients.models import Cliente, PuntosFidelizacion
from .models import Venta, VentaDetalle, Pago
from .forms import ProductoSearchForm, VentaForm
from users.decorators import check_user_role
from django.core.mail import EmailMessage
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt

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
            
            lote.cantidad_disponible -= cantidad
            lote.save()
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
