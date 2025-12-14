from django.shortcuts import render, get_object_or_404
from decimal import Decimal
import json
from django.db import transaction
from django.db.models import Sum, F, Count, Avg
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.template.loader import render_to_string
from django.contrib import messages
from django.conf import settings
from weasyprint import HTML
from inventory.models import Producto, Lote, MovimientoInventario
from clients.models import Cliente, PuntosFidelizacion
from .models import Venta, VentaDetalle, Pago, Mesa, ItemMesa
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
    from inventory.models import Categoria
    from django.db.models import Count, Sum, Q
    
    # Obtener categorías con conteo de productos disponibles
    categorias = Categoria.objects.annotate(
        total_productos=Count('producto', filter=Q(producto__stock_actual__gt=0))
    ).filter(total_productos__gt=0).order_by('nombre')
    
    # Si se selecciona una categoría, cargar sus productos
    categoria_id = request.GET.get('categoria')
    productos = None
    categoria_seleccionada = None
    
    if categoria_id:
        try:
            categoria_seleccionada = Categoria.objects.get(id=categoria_id)
            productos = Producto.objects.filter(
                categoria_id=categoria_id,
                stock_actual__gt=0
            ).select_related('categoria').order_by('nombre')
        except Categoria.DoesNotExist:
            pass
    
    search_form = ProductoSearchForm()
    venta_form = VentaForm()
    
    # Cargar clientes para el selector (excluyendo Consumidor Final que se muestra por defecto)
    clientes = Cliente.objects.exclude(id=1).order_by('nombres', 'apellidos')
    
    context = {
        'categorias': categorias,
        'productos': productos,
        'categoria_seleccionada': categoria_seleccionada,
        'search_form': search_form,
        'venta_form': venta_form,
        'clientes': clientes,
    }
    return render(request, 'pos/pos_main.html', context)

@login_required
def listar_ventas(request):
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    from django.utils import timezone
    
    # Si es vendedor, solo ver sus propias ventas
    if request.user.rol.nombre == 'Vendedor':
        ventas = Venta.objects.filter(usuario=request.user).select_related('cliente', 'usuario').prefetch_related('pago_set').order_by('-fecha_venta')
    else:
        ventas = Venta.objects.select_related('cliente', 'usuario').prefetch_related('pago_set').order_by('-fecha_venta')

    # Filtro por rango de fechas
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if fecha_desde:
        try:
            # Convertir a datetime con hora 00:00:00 y hacer timezone-aware
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            fecha_desde_aware = timezone.make_aware(fecha_desde_dt.replace(hour=0, minute=0, second=0))
            ventas = ventas.filter(fecha_venta__gte=fecha_desde_aware)
        except Exception as e:
            print(f"Error en fecha_desde: {e}")
            pass
    
    if fecha_hasta:
        try:
            # Convertir a datetime con hora 23:59:59 y hacer timezone-aware
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            fecha_hasta_aware = timezone.make_aware(fecha_hasta_dt.replace(hour=23, minute=59, second=59))
            ventas = ventas.filter(fecha_venta__lte=fecha_hasta_aware)
        except Exception as e:
            print(f"Error en fecha_hasta: {e}")
            pass

    # Filtro por método de pago
    metodo_pago = request.GET.get('metodo_pago')
    if metodo_pago:
        ventas = ventas.filter(pago__metodo_pago=metodo_pago).distinct()

    # Filtro por canal de venta
    canal_venta = request.GET.get('canal_venta')
    if canal_venta:
        ventas = ventas.filter(canal_venta=canal_venta)

    # Paginación
    items_por_pagina = request.GET.get('items', 10)
    try:
        items_por_pagina = int(items_por_pagina)
        if items_por_pagina not in [10, 20, 50, 100]:
            items_por_pagina = 10
    except (ValueError, TypeError):
        items_por_pagina = 10

    paginator = Paginator(ventas, items_por_pagina)
    page = request.GET.get('page', 1)

    try:
        ventas_paginadas = paginator.page(page)
    except PageNotAnInteger:
        ventas_paginadas = paginator.page(1)
    except EmptyPage:
        ventas_paginadas = paginator.page(paginator.num_pages)

    context = {
        'ventas': ventas_paginadas,
        'total_ventas': paginator.count,
        'items_por_pagina': items_por_pagina,
    }

    return render(request, 'pos/listar_ventas.html', context)

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
            'total': float(total_venta),
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
    """
    Envía factura por correo usando las utilidades mejoradas
    """
    from core.email_utils import send_invoice_email
    
    venta = get_object_or_404(Venta.objects.select_related('cliente', 'usuario'), pk=venta_id)
    
    # Usar las nuevas utilidades de correo
    result = send_invoice_email(venta)
    
    if result['success']:
        # Si es Railway fallback, mostrar mensaje especial
        if result.get('railway_blocked'):
            return JsonResponse({
                'success': True, 
                'mensaje': result['message'],
                'method': result['method'],
                'railway_blocked': True,
                'help_url': '/pos/emails-pendientes/'
            })
        else:
            return JsonResponse({
                'success': True, 
                'mensaje': result['message'],
                'method': result['method']
            })
    else:
        return JsonResponse({
            'success': False, 
            'error': result['message'],
            'method': result['method']
        }, status=400)

def debug_email_config(request):
    """
    Vista de debug para mostrar toda la configuración de correo
    """
    import os
    import socket
    
    # Configuración actual
    debug_info = {
        'environment': {
            'DEBUG_env': os.environ.get('DEBUG', 'No definido'),
            'BREVO_API_KEY_env': 'Configurado (' + os.environ.get('BREVO_API_KEY', '')[:10] + '...)' if os.environ.get('BREVO_API_KEY') else 'NO CONFIGURADO - AGREGAR EN RAILWAY',
            'DEFAULT_FROM_EMAIL_env': os.environ.get('DEFAULT_FROM_EMAIL', 'No definido'),
        },
        'django_config': {
            'DEBUG': settings.DEBUG,
            'EMAIL_BACKEND': settings.EMAIL_BACKEND,
            'EMAIL_HOST': settings.EMAIL_HOST,
            'EMAIL_PORT': settings.EMAIL_PORT,
            'EMAIL_USE_TLS': settings.EMAIL_USE_TLS,
            'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
            'EMAIL_HOST_PASSWORD': 'Configurado (' + str(len(getattr(settings, 'EMAIL_HOST_PASSWORD', '') or '')) + ' chars)' if getattr(settings, 'EMAIL_HOST_PASSWORD', None) else 'NO CONFIGURADO',
            'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
            'EMAIL_TIMEOUT': getattr(settings, 'EMAIL_TIMEOUT', 'No definido'),
        },
        'test_result': None,
        'test_url': '?test=1'
    }
    
    # Intentar enviar correo de prueba si se solicita
    if request.GET.get('test') == '1':
        # Timeout corto para no quedarse colgado
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(10)  # 10 segundos máximo
        
        try:
            from django.core.mail import send_mail
            
            # Enviar correo de prueba (a tu email registrado en Resend)
            test_email = request.GET.get('email', 'michaeldaramirez117@gmail.com')
            send_mail(
                subject='Test desde Railway - La Playita',
                message='Este es un correo de prueba desde Railway usando API HTTP de Resend.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[test_email],
                fail_silently=False,
            )
            
            debug_info['test_result'] = {
                'success': True, 
                'message': 'Correo enviado exitosamente via ' + settings.EMAIL_BACKEND
            }
            
        except Exception as e:
            debug_info['test_result'] = {
                'success': False, 
                'error': str(e), 
                'type': type(e).__name__
            }
        finally:
            socket.setdefaulttimeout(old_timeout)
    
    return JsonResponse(debug_info, json_dumps_params={'indent': 2})

@login_required
def test_email_config(request):
    """
    Vista para probar la configuración de correo con soporte para Resend
    """
    from core.email_utils import test_email_configuration, send_email_with_fallback
    
    if request.method == 'POST':
        # Probar enviando un correo de prueba
        test_email = request.POST.get('test_email', request.user.email)
        
        if not test_email:
            return JsonResponse({
                'success': False,
                'message': 'Email de prueba requerido'
            })
        
        # HTML mejorado para el correo de prueba
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Prueba de Correo - La Playita</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                <h1>🏪 La Playita POS</h1>
                <h2>Prueba de Configuración de Correo</h2>
            </div>
            
            <div style="padding: 20px; background: #f9f9f9; margin: 20px 0; border-radius: 10px;">
                <p><strong>¡Felicidades!</strong> Si estás leyendo este mensaje, significa que:</p>
                <ul>
                    <li>✅ La configuración de correo está funcionando correctamente</li>
                    <li>✅ Resend está enviando correos exitosamente</li>
                    <li>✅ El sistema está listo para enviar facturas</li>
                </ul>
                
                <p><strong>Detalles de la prueba:</strong></p>
                <ul>
                    <li>Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li>Usuario: {request.user.username}</li>
                    <li>Proveedor: {getattr(settings, 'EMAIL_PROVIDER', 'resend')}</li>
                </ul>
            </div>
            
            <div style="text-align: center; color: #666; font-size: 0.9em;">
                <p>Este es un correo automático de prueba del sistema La Playita POS</p>
            </div>
        </body>
        </html>
        """
        
        result = send_email_with_fallback(
            subject="✅ Prueba de correo exitosa - La Playita POS",
            message="Este es un correo de prueba para verificar la configuración de Resend.",
            recipient_list=[test_email],
            html_message=html_content
        )
        
        return JsonResponse(result)
    
    # GET: Mostrar información de configuración
    config_test = test_email_configuration()
    
    return JsonResponse({
        'config_test': config_test,
        'user_email': request.user.email or 'No disponible',
        'debug_mode': settings.DEBUG,
        'email_provider': getattr(settings, 'EMAIL_PROVIDER', 'resend'),
        'resend_configured': bool(getattr(settings, 'RESEND_API_KEY', None))
    })

@login_required
def configurar_resend(request):
    """
    Vista para mostrar la página de configuración de Resend
    """
    context = {
        'debug_mode': settings.DEBUG,
        'email_provider': getattr(settings, 'EMAIL_PROVIDER', 'resend'),
        'resend_configured': bool(getattr(settings, 'RESEND_API_KEY', None)),
        'use_console_email': getattr(settings, 'USE_CONSOLE_EMAIL', False),
        'current_backend': settings.EMAIL_BACKEND,
        'current_host': getattr(settings, 'EMAIL_HOST', 'No configurado'),
        'current_port': getattr(settings, 'EMAIL_PORT', 'No configurado'),
        'current_user': getattr(settings, 'EMAIL_HOST_USER', 'No configurado'),
        'current_password_set': bool(getattr(settings, 'EMAIL_HOST_PASSWORD', None)),
        'default_from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'No configurado')
    }
    return render(request, 'pos/test_resend.html', context)

@login_required
def railway_status(request):
    """
    Vista para verificar el estado de la configuración en Railway
    """
    import os
    
    # Verificar configuración
    is_railway = not settings.DEBUG
    email_provider = getattr(settings, 'EMAIL_PROVIDER', 'gmail')
    resend_configured = bool(getattr(settings, 'RESEND_API_KEY', None))
    
    status = {
        'environment': 'Railway (Producción)' if is_railway else 'Desarrollo Local',
        'email_provider': email_provider,
        'resend_configured': resend_configured,
        'gmail_fallback': email_provider == 'gmail' or (email_provider == 'resend' and not resend_configured),
        'ready_for_railway': resend_configured if is_railway else True,
        'recommendations': []
    }
    
    # Generar recomendaciones
    if is_railway and not resend_configured:
        status['recommendations'].append({
            'type': 'warning',
            'message': 'Configura RESEND_API_KEY en Railway para envío confiable de correos',
            'action': 'Agregar variable EMAIL_PROVIDER=resend y RESEND_API_KEY=tu_api_key'
        })
    
    if not is_railway and email_provider == 'resend' and not resend_configured:
        status['recommendations'].append({
            'type': 'info',
            'message': 'Usando Gmail como fallback en desarrollo (normal)',
            'action': 'Configura RESEND_API_KEY para probar Resend localmente'
        })
    
    return JsonResponse(status, json_dumps_params={'indent': 2})

@login_required
def emails_pendientes(request):
    """
    Vista para mostrar correos que no se pudieron enviar
    """
    import os
    
    log_file = os.path.join(settings.BASE_DIR, 'emails_pendientes.log')
    emails_pendientes = []
    
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parsear el contenido del log
            email_blocks = content.split('=' * 50)
            for block in email_blocks:
                if block.strip():
                    lines = block.strip().split('\n')
                    email_data = {}
                    for line in lines:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            email_data[key.strip()] = value.strip()
                    
                    if email_data:
                        emails_pendientes.append(email_data)
    
    except Exception as e:
        messages.error(request, f'Error leyendo correos pendientes: {e}')
    
    return render(request, 'pos/emails_pendientes.html', {
        'emails_pendientes': emails_pendientes,
        'total_pendientes': len(emails_pendientes)
    })

@csrf_exempt
@login_required
def crear_cliente(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validar campos requeridos
            campos_requeridos = ['documento', 'nombres', 'apellidos', 'correo', 'telefono']
            for campo in campos_requeridos:
                if not data.get(campo):
                    return JsonResponse({'success': False, 'error': f'El campo {campo} es requerido'}, status=400)
            
            # Verificar si ya existe un cliente con el mismo documento
            if Cliente.objects.filter(documento=data['documento']).exists():
                return JsonResponse({'success': False, 'error': 'Ya existe un cliente con este documento'}, status=400)
            
            # Verificar si ya existe un cliente con el mismo correo
            if Cliente.objects.filter(correo=data['correo']).exists():
                return JsonResponse({'success': False, 'error': 'Ya existe un cliente con este correo electrónico'}, status=400)
            
            cliente = Cliente.objects.create(
                documento=data['documento'],
                nombres=data['nombres'],
                apellidos=data['apellidos'],
                correo=data['correo'],
                telefono=data['telefono']
            )
            return JsonResponse({'success': True, 'cliente_id': cliente.id})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Datos JSON inválidos'}, status=400)
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
    
    # Determinar si es vendedor para filtrar sus propias ventas
    es_vendedor = request.user.rol.nombre == 'Vendedor'
    filtro_usuario = {'usuario': request.user} if es_vendedor else {}
    
    # Datos de inventario para accesos rápidos
    total_productos = Producto.objects.count()
    
    # Listas de productos con alertas
    lista_productos_stock_bajo = Producto.objects.filter(stock_actual__lt=F('stock_minimo')).order_by('stock_actual')[:10]
    productos_bajos_stock = lista_productos_stock_bajo.count()
    
    lista_productos_agotados = Producto.objects.filter(stock_actual=0).order_by('nombre')[:10]
    productos_agotados = lista_productos_agotados.count()
    
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
    
    lista_productos_sin_movimiento = Producto.objects.exclude(
        id__in=productos_vendidos
    ).filter(stock_actual__gt=0).order_by('nombre')[:10]
    productos_sin_movimiento = lista_productos_sin_movimiento.count()
    
    # Ventas del día
    ventas_hoy = Venta.objects.filter(fecha_venta__gte=hoy_inicio, **filtro_usuario)
    total_hoy = ventas_hoy.aggregate(Sum('total_venta'))['total_venta__sum'] or Decimal('0')
    cantidad_hoy = ventas_hoy.count()
    
    # Ventas últimos 7 días
    ventas_7dias = Venta.objects.filter(fecha_venta__gte=hace_7_dias, **filtro_usuario)
    total_7dias = ventas_7dias.aggregate(Sum('total_venta'))['total_venta__sum'] or Decimal('0')
    cantidad_7dias = ventas_7dias.count()
    
    # Ventas últimos 30 días
    ventas_30dias = Venta.objects.filter(fecha_venta__gte=hace_30_dias, **filtro_usuario)
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
        venta__fecha_venta__gte=hace_30_dias,
        **{f'venta__{k}': v for k, v in filtro_usuario.items()}
    ).values('producto__nombre').annotate(
        cantidad_total=Sum('cantidad'),
        ingresos=Sum('subtotal')
    ).order_by('-cantidad_total')[:5]
    
    # Top 5 vendedores (solo para administradores)
    if not es_vendedor:
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
    else:
        top_vendedores = []
    
    # Top 5 clientes (últimos 30 días)
    top_clientes = Venta.objects.filter(
        fecha_venta__gte=hace_30_dias,
        **filtro_usuario
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
    
    # Ventas por fecha (últimos 30 días) para el gráfico
    import json
    from collections import defaultdict
    
    ventas_por_fecha_dict = defaultdict(lambda: {'total': Decimal('0'), 'cantidad': 0})
    
    for venta in Venta.objects.filter(fecha_venta__gte=hace_30_dias, **filtro_usuario):
        fecha_str = venta.fecha_venta.date().strftime('%Y-%m-%d')
        ventas_por_fecha_dict[fecha_str]['total'] += venta.total_venta
        ventas_por_fecha_dict[fecha_str]['cantidad'] += 1
    
    # Ordenar por fecha
    ventas_ordenadas = sorted(ventas_por_fecha_dict.items())
    
    # Preparar datos para el gráfico
    ventas_fechas = [fecha for fecha, _ in ventas_ordenadas]
    ventas_totales = [float(datos['total']) for _, datos in ventas_ordenadas]
    
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
        'ventas_fechas_json': json.dumps(ventas_fechas),
        'ventas_totales_json': json.dumps(ventas_totales),
        'lista_productos_stock_bajo': lista_productos_stock_bajo,
        'lista_productos_agotados': lista_productos_agotados,
        'lista_productos_sin_movimiento': lista_productos_sin_movimiento,
        'es_vendedor': es_vendedor,
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


# ==================== GESTIÓN DE MESAS ====================

@login_required
def api_listar_mesas(request):
    """API para listar todas las mesas con su estado"""
    from .models import Mesa
    
    mesas = Mesa.objects.filter(activa=True).order_by('numero')
    
    mesas_data = []
    for mesa in mesas:
        mesas_data.append({
            'id': mesa.id,
            'numero': mesa.numero,
            'nombre': mesa.nombre,
            'capacidad': mesa.capacidad,
            'estado': mesa.estado,
            'cuenta_abierta': mesa.cuenta_abierta,
            'total_cuenta': float(mesa.total_cuenta),
            'cliente': {
                'id': mesa.cliente.id,
                'nombre': f"{mesa.cliente.nombres} {mesa.cliente.apellidos}"
            } if mesa.cliente else None
        })
    
    return JsonResponse({'success': True, 'mesas': mesas_data})


@login_required
@require_POST
def api_crear_mesa(request):
    """API para crear una nueva mesa"""
    from .models import Mesa
    
    try:
        data = json.loads(request.body)
        nombre = data.get('nombre', '').strip()
        descripcion = data.get('descripcion', '').strip()
        capacidad = 4  # Capacidad fija por defecto
        
        # Si no se proporciona nombre, usar un nombre por defecto basado en el ID
        if not nombre:
            # Crear la mesa primero para obtener el ID
            mesa = Mesa.objects.create(
                numero='temp',  # Temporal
                nombre='temp',  # Temporal
                capacidad=capacidad,
                estado=Mesa.ESTADO_DISPONIBLE,
                activa=True,
                cuenta_abierta=False,
                total_cuenta=Decimal('0.00')
            )
            
            # Ahora usar el ID para generar nombre y número únicos
            nombre = f'Mesa {mesa.id}'
            numero = str(mesa.id)
            
            # Actualizar con los valores correctos
            mesa.numero = numero
            mesa.nombre = nombre
            mesa.save()
        else:
            # Crear mesa con nombre personalizado
            mesa = Mesa.objects.create(
                numero='temp',  # Temporal
                nombre='temp',  # Temporal
                capacidad=capacidad,
                estado=Mesa.ESTADO_DISPONIBLE,
                activa=True,
                cuenta_abierta=False,
                total_cuenta=Decimal('0.00')
            )
            
            # Usar el ID como número único
            numero = str(mesa.id)
            
            # Si hay descripción, agregarla
            if descripcion:
                nombre_final = f"{nombre} ({descripcion})"
            else:
                nombre_final = nombre
            
            # Actualizar con los valores correctos
            mesa.numero = numero
            mesa.nombre = nombre_final
            mesa.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Mesa "{mesa.nombre}" creada correctamente',
            'mesa': {
                'id': mesa.id,
                'numero': mesa.numero,
                'nombre': mesa.nombre,
                'capacidad': mesa.capacidad
            }
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def api_editar_mesa(request, mesa_id):
    """API para editar una mesa existente"""
    from .models import Mesa
    
    try:
        data = json.loads(request.body)
        mesa = get_object_or_404(Mesa, pk=mesa_id)
        
        if mesa.cuenta_abierta:
            return JsonResponse({'success': False, 'error': 'No se puede editar una mesa con cuenta abierta'}, status=400)
        
        nombre = data.get('nombre', '').strip()
        descripcion = data.get('descripcion', '').strip()
        
        if not nombre:
            return JsonResponse({'success': False, 'error': 'El nombre de la mesa es obligatorio'}, status=400)
        
        # Actualizar nombre con descripción si se proporciona
        if descripcion:
            mesa.nombre = f"{nombre} ({descripcion})"
        else:
            mesa.nombre = nombre
        
        mesa.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Mesa "{mesa.nombre}" actualizada correctamente'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def api_eliminar_mesa(request, mesa_id):
    """API para eliminar (desactivar) una mesa"""
    from .models import Mesa
    
    try:
        mesa = get_object_or_404(Mesa, pk=mesa_id)
        
        if mesa.cuenta_abierta:
            return JsonResponse({'success': False, 'error': 'No se puede eliminar una mesa con cuenta abierta'}, status=400)
        
        mesa.activa = False
        mesa.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Mesa {mesa.numero} eliminada correctamente'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def api_abrir_mesa(request, mesa_id):
    """API para abrir una mesa"""
    from .models import Mesa
    
    try:
        data = json.loads(request.body)
        mesa = get_object_or_404(Mesa, pk=mesa_id)
        
        if mesa.cuenta_abierta:
            return JsonResponse({'success': False, 'error': 'La mesa ya tiene una cuenta abierta'}, status=400)
        
        cliente_id = data.get('cliente_id', 1)
        cliente = get_object_or_404(Cliente, pk=cliente_id)
        
        mesa.cuenta_abierta = True
        mesa.estado = Mesa.ESTADO_OCUPADA
        mesa.cliente = cliente
        mesa.fecha_apertura = timezone.now()
        mesa.total_cuenta = Decimal('0.00')
        mesa.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Mesa {mesa.numero} abierta correctamente',
            'mesa_numero': mesa.numero
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def api_agregar_item_mesa(request, mesa_id):
    """API para agregar items a una mesa"""
    from .models import Mesa, ItemMesa
    
    try:
        data = json.loads(request.body)
        mesa = get_object_or_404(Mesa, pk=mesa_id)
        
        if not mesa.cuenta_abierta:
            return JsonResponse({'success': False, 'error': 'La mesa no tiene una cuenta abierta'}, status=400)
        
        items = data.get('items', [])
        
        for item_data in items:
            producto = get_object_or_404(Producto, pk=item_data['producto_id'])
            lote = get_object_or_404(Lote, pk=item_data['lote_id'])
            cantidad = int(item_data['cantidad'])
            anotacion = item_data.get('anotacion', '')
            
            subtotal = producto.precio_unitario * cantidad
            
            ItemMesa.objects.create(
                mesa=mesa,
                producto=producto,
                lote=lote,
                cantidad=cantidad,
                precio_unitario=producto.precio_unitario,
                subtotal=subtotal,
                anotacion=anotacion
            )
        
        # Actualizar total de la mesa
        from .models import ItemMesa
        total = ItemMesa.objects.filter(mesa=mesa, facturado=False).aggregate(
            Sum('subtotal')
        )['subtotal__sum'] or Decimal('0.00')
        
        mesa.total_cuenta = total
        mesa.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Items agregados correctamente',
            'total_cuenta': float(total)
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def api_items_mesa(request, mesa_id):
    """API para obtener los items de una mesa"""
    from .models import Mesa, ItemMesa
    
    mesa = get_object_or_404(Mesa, pk=mesa_id)
    items = ItemMesa.objects.filter(mesa=mesa, facturado=False).select_related('producto', 'lote')
    
    items_data = []
    for item in items:
        items_data.append({
            'id': item.id,
            'producto': item.producto.nombre,
            'producto_id': item.producto.id,
            'lote_id': item.lote.id if item.lote else None,
            'cantidad': item.cantidad,
            'precio_unitario': float(item.precio_unitario),
            'subtotal': float(item.subtotal),
            'anotacion': item.anotacion or ''
        })
    
    return JsonResponse({
        'success': True,
        'items': items_data,
        'total': float(mesa.total_cuenta),
        'mesa_numero': mesa.numero
    })


@login_required
@require_POST
def api_editar_item_mesa(request, item_id):
    """API para editar la anotación de un item de mesa"""
    from .models import ItemMesa
    
    try:
        data = json.loads(request.body)
        item = get_object_or_404(ItemMesa, pk=item_id)
        
        if item.facturado:
            return JsonResponse({'success': False, 'error': 'No se puede editar un item ya facturado'}, status=400)
        
        item.anotacion = data.get('anotacion', '')
        item.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Anotación actualizada correctamente'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def api_eliminar_item_mesa(request, item_id):
    """API para eliminar un item de una mesa"""
    from .models import ItemMesa
    
    try:
        item = get_object_or_404(ItemMesa, pk=item_id)
        mesa = item.mesa
        
        if item.facturado:
            return JsonResponse({'success': False, 'error': 'No se puede eliminar un item ya facturado'}, status=400)
        
        item.delete()
        
        # Recalcular total de la mesa
        total = ItemMesa.objects.filter(mesa=mesa, facturado=False).aggregate(
            Sum('subtotal')
        )['subtotal__sum'] or Decimal('0.00')
        
        mesa.total_cuenta = total
        mesa.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Item eliminado correctamente',
            'total_cuenta': float(total)
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
@transaction.atomic
def api_cerrar_mesa(request, mesa_id):
    """API para cerrar una mesa y generar la venta"""
    from .models import Mesa, ItemMesa
    
    try:
        data = json.loads(request.body)
        print(f"DEBUG - Datos recibidos en cerrar mesa: {data}")
        
        mesa = get_object_or_404(Mesa, pk=mesa_id)
        
        if not mesa.cuenta_abierta:
            return JsonResponse({'success': False, 'error': 'La mesa no tiene una cuenta abierta'}, status=400)
        
        items = ItemMesa.objects.filter(mesa=mesa, facturado=False)
        
        if not items.exists():
            return JsonResponse({'success': False, 'error': 'No hay items en la mesa'}, status=400)
        
        # Obtener el cliente del request o usar el de la mesa como fallback
        cliente_id = data.get('cliente_id')
        print(f"DEBUG - Cliente ID recibido: {cliente_id}")
        print(f"DEBUG - Cliente de la mesa: {mesa.cliente}")
        
        if cliente_id:
            cliente = get_object_or_404(Cliente, pk=cliente_id)
            print(f"DEBUG - Usando cliente del request: {cliente}")
        else:
            cliente = mesa.cliente if mesa.cliente else get_object_or_404(Cliente, pk=1)
            print(f"DEBUG - Usando cliente fallback: {cliente}")
        
        # Crear la venta
        nueva_venta = Venta.objects.create(
            cliente=cliente,
            usuario=request.user,
            canal_venta='mostrador',
            total_venta=mesa.total_cuenta
        )
        
        # Crear el pago
        Pago.objects.create(
            venta=nueva_venta,
            monto=mesa.total_cuenta,
            metodo_pago=data.get('metodo_pago', 'efectivo'),
            estado='completado'
        )
        
        # Crear detalles de venta y actualizar lotes
        for item in items:
            VentaDetalle.objects.create(
                venta=nueva_venta,
                producto=item.producto,
                lote=item.lote,
                cantidad=item.cantidad,
                subtotal=item.subtotal
            )
            
            # Actualizar lote
            item.lote.cantidad_disponible -= item.cantidad
            item.lote.save()
            
            # Registrar movimiento de inventario
            MovimientoInventario.objects.create(
                producto=item.producto,
                lote=item.lote,
                cantidad=-item.cantidad,
                tipo_movimiento='salida',
                descripcion=f'Venta Mesa {mesa.numero} - Venta #{nueva_venta.id}',
                venta=nueva_venta
            )
            
            # Marcar item como facturado
            item.facturado = True
            item.save()
        
        # Cerrar y eliminar la mesa
        mesa.cuenta_abierta = False
        mesa.estado = Mesa.ESTADO_DISPONIBLE
        mesa.total_cuenta = Decimal('0.00')
        mesa.cliente = None
        mesa.fecha_apertura = None
        mesa.activa = False  # Desactivar la mesa (eliminarla)
        mesa.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Mesa {mesa.numero} cerrada correctamente',
            'venta_id': nueva_venta.id
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
def api_editar_item_mesa(request, mesa_id, item_id):
    """API para editar la anotación de un item de mesa"""
    try:
        data = json.loads(request.body)
        
        # Obtener el item
        item = ItemMesa.objects.get(id=item_id, mesa_id=mesa_id)
        
        # Actualizar la anotación
        item.anotacion = data.get('anotacion', '')
        item.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Comentario actualizado correctamente'
        })
    
    except ItemMesa.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
def api_eliminar_item_mesa(request, mesa_id, item_id):
    """API para eliminar un item de una mesa"""
    try:
        # Obtener el item
        item = ItemMesa.objects.get(id=item_id, mesa_id=mesa_id)
        mesa = item.mesa
        
        # Guardar el subtotal antes de eliminar
        subtotal = item.subtotal
        
        # Eliminar el item
        item.delete()
        
        # Recalcular el total de la mesa
        mesa.total_cuenta = ItemMesa.objects.filter(
            mesa=mesa,
            facturado=False
        ).aggregate(
            total=Sum('subtotal')
        )['total'] or Decimal('0.00')
        mesa.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Producto eliminado correctamente',
            'nuevo_total': float(mesa.total_cuenta)
        })
    
    except ItemMesa.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)






