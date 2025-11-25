from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.templatetags.static import static
from django.contrib.staticfiles.finders import find as find_static
import os
from datetime import datetime
from django.utils import timezone
from django.db import transaction, connection
import json
from email.mime.image import MIMEImage # Import MIMEImage

from django.core.serializers.json import DjangoJSONEncoder
from users.decorators import check_user_role
from .models import Proveedor, Reabastecimiento, ReabastecimientoDetalle
from inventory.models import Producto, Categoria, Lote, MovimientoInventario, TasaIVA
from inventory.forms import ReabastecimientoForm, ReabastecimientoDetalleFormSet, ProductoForm

# --- Vistas de Proveedores ---

@login_required
@check_user_role(allowed_roles=['Administrador'])
def proveedor_list(request):
    """
    Vista para listar todos los proveedores.
    """
    proveedores = Proveedor.objects.all()
    return render(request, 'suppliers/proveedor_list.html', {'proveedores': proveedores})

@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador'])
def proveedor_create_ajax(request):
    """
    Vista para crear un proveedor vía AJAX.
    """
    try:
        data = json.loads(request.body)
        proveedor = Proveedor.objects.create(
            tipo_documento=data['tipo_documento'],
            documento_identificacion=data['documento_identificacion'],
            nombre_empresa=data['nombre_empresa'],
            telefono=data.get('telefono', ''),
            correo=data.get('correo', ''),
            direccion=data.get('direccion', '')
        )
        return JsonResponse({
            'id': proveedor.id,
            'nombre_empresa': proveedor.nombre_empresa
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# --- Vistas de Reabastecimientos ---

def send_supply_request_email(request, reabastecimiento):
    proveedor = reabastecimiento.proveedor
    if proveedor.correo:
        subject = f'Solicitud de Reabastecimiento #{reabastecimiento.id}'
        context = {
            'reabastecimiento': reabastecimiento,
            'proveedor_nombre': proveedor.nombre_empresa,
            'current_year': datetime.now().year,
            'logo_src': 'cid:logo', # Use cid for embedded image
        }
        html_content = render_to_string('suppliers/emails/reabastecimiento_solicitud.html', context)
        text_content = f"Estimado/a {proveedor.nombre_empresa}, se ha generado una nueva solicitud de reabastecimiento."
        
        msg = EmailMultiAlternatives(subject, text_content, None, [proveedor.correo])
        msg.attach_alternative(html_content, "text/html")

        # Attach logo image
        logo_path = find_static('core/img/la-playita-logo.png')
        print(f"DEBUG: logo_path found by find_static: {logo_path}")
        if logo_path and os.path.exists(logo_path):
            print(f"DEBUG: logo file exists at: {logo_path}")
            with open(logo_path, 'rb') as f:
                logo_image = MIMEImage(f.read())
                logo_image.add_header('Content-ID', '<logo>') # Set Content-ID
                msg.attach(logo_image)
        else:
            print(f"DEBUG: logo file NOT found or path is None. logo_path: {logo_path}, os.path.exists: {os.path.exists(logo_path) if logo_path else 'N/A'}")
        
        msg.send()

# New function to send discrepancy email
def send_discrepancy_email(reabastecimiento, discrepancias):
    """
    Sends an email notification about discrepancies in a received restock.
    """
    # Assuming there's an internal email for notifications, or send to admin
    # For now, let's just print the email content to console
    subject = f'Discrepancia en Reabastecimiento #{reabastecimiento.id}'
    
    context = {
        'reabastecimiento': reabastecimiento,
        'proveedor_nombre': reabastecimiento.proveedor.nombre_empresa,
        'discrepancias': discrepancias,
        'current_year': datetime.now().year,
        'logo_src': 'cid:logo', # Use cid for embedded image
    }
    
    html_content = render_to_string('suppliers/emails/reabastecimiento_discrepancia.html', context)
    text_content = (
        f"Estimado/a, se ha detectado una discrepancia en el reabastecimiento #{reabastecimiento.id}.\n"
        f"Proveedor: {reabastecimiento.proveedor.nombre_empresa}\n"
        "Detalles de la discrepancia:\n"
    )
    for disc in discrepancias:
        text_content += (
            f"- Producto: {disc['producto_nombre']}, Solicitado: {disc['cantidad_solicitada']}, "
            f"Recibido: {disc['cantidad_recibida']}\n"
        )

    # TODO: Replace with actual recipient list (e.g., admin emails) 
    recipient_list = ["admin@example.com"] 
    if reabastecimiento.proveedor.correo:
        recipient_list.append(reabastecimiento.proveedor.correo)

    msg = EmailMultiAlternatives(subject, text_content, None, recipient_list)
    msg.attach_alternative(html_content, "text/html")

    # Attach logo image
    logo_path = find_static('core/img/la-playita-logo.png')
    if logo_path and os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            logo_image = MIMEImage(f.read())
            logo_image.add_header('Content-ID', '<logo>') # Set Content-ID
            msg.attach(logo_image)
    
    msg.send()
    print(f"DEBUG: Discrepancy email sent for Reabastecimiento #{reabastecimiento.id}")

@never_cache
@login_required
@check_user_role(allowed_roles=['Administrador'])
def reabastecimiento_list(request):
    """
    Lista los reabastecimientos y maneja el formulario para crear uno nuevo.
    """
    reabs = (
        Reabastecimiento.objects
        .exclude(estado=Reabastecimiento.ESTADO_CANCELADO)
        .select_related('proveedor')
        .prefetch_related(
            'reabastecimientodetalle_set__producto__categoria',
            'reabastecimientodetalle_set__lote_set__ventadetalle_set'
        )
        .order_by('-fecha'))

    for reab in reabs:
        reab.tiene_ventas = any(
            lote.ventadetalle_set.exists()
            for detalle in reab.reabastecimientodetalle_set.all()
            for lote in detalle.lote_set.all()
    )

    form = ReabastecimientoForm(initial_creation=True)
    formset = ReabastecimientoDetalleFormSet(queryset=ReabastecimientoDetalle.objects.none())

    productos_data = list(Producto.objects.values('id', 'precio_unitario'))
    all_products_data = list(Producto.objects.values('id', 'nombre'))
    categorias = Categoria.objects.all()
    tasas_iva = TasaIVA.objects.all()

    context = {
        'reabastecimientos': reabs,
        'form': form,
        'formset': formset,
        'products_json': json.dumps(productos_data, cls=DjangoJSONEncoder),
        'all_products_json': json.dumps(all_products_data),
        'categorias': categorias,
        'tasas_iva': tasas_iva,
    }
    return render(request, 'suppliers/reabastecimiento_list.html', context)

@never_cache
@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador'])
def reabastecimiento_create(request):
    """
    Crear un reabastecimiento con múltiples detalles.
    """
    form = ReabastecimientoForm(request.POST)
    formset = ReabastecimientoDetalleFormSet(request.POST, queryset=ReabastecimientoDetalle.objects.none())
    if form.is_valid() and formset.is_valid():
        try:
            with transaction.atomic():
                reab = form.save(commit=False)
                reab.estado = Reabastecimiento.ESTADO_SOLICITADO
                
                total_costo = 0
                total_iva = 0
                
                detalles_a_crear = []
                for detalle_form in formset.cleaned_data:
                    if detalle_form and not detalle_form.get('DELETE'):
                        cantidad = detalle_form['cantidad']
                        costo_unitario = detalle_form['costo_unitario']
                        producto = detalle_form['producto']
                        
                        subtotal = cantidad * costo_unitario
                        
                        # Obtener el porcentaje de IVA del producto
                        tasa_iva_porcentaje = producto.tasa_iva.porcentaje
                        iva_detalle = subtotal * (tasa_iva_porcentaje / 100)
                        
                        total_costo += subtotal
                        total_iva += iva_detalle
                        
                        detalle_form['iva'] = iva_detalle
                        detalles_a_crear.append(detalle_form)

                if total_costo == 0:
                    return JsonResponse({'error': 'Debe agregar al menos un detalle de producto.'}, status=400)

                reab.costo_total = total_costo
                reab.iva = total_iva
                reab.save()

                detalles_data = []
                for detalle_form in detalles_a_crear:
                    detalle_form.pop('reabastecimiento', None)
                    detalle_form.pop('DELETE', None)
                    detalle = ReabastecimientoDetalle.objects.create(reabastecimiento=reab, **detalle_form)
                    detalles_data.append({
                        'producto_nombre': detalle.producto.nombre,
                        'categoria_nombre': detalle.producto.categoria.nombre,
                        'cantidad': detalle.cantidad,
                        'costo_unitario': float(detalle.costo_unitario),
                        'subtotal': float(detalle.cantidad * detalle.costo_unitario),
                        'iva': float(detalle.iva),
                        'estado_lote': 'No recibido'
                    })

                if reab.estado == Reabastecimiento.ESTADO_SOLICITADO:
                    send_supply_request_email(request, reab)

                return JsonResponse({
                    'id': reab.id, 'fecha': reab.fecha.isoformat(),
                    'proveedor': reab.proveedor.nombre_empresa, 
                    'costo_total': float(reab.costo_total),
                    'iva': float(reab.iva),
                    'forma_pago': reab.get_forma_pago_display(), 'estado': reab.get_estado_display(),
                    'observaciones': reab.observaciones, 'detalles': detalles_data
                })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        errors = form.errors.as_json()
        formset_errors = [f.errors.as_json() for f in formset.forms if f.errors]
        return JsonResponse({'errors': errors, 'formset_errors': formset_errors}, status=400)

@never_cache
@login_required
@check_user_role(allowed_roles=['Administrador'])
def reabastecimiento_editar(request, pk):
    """Vista para obtener datos de un reabastecimiento para editar."""
    try:
        reab = Reabastecimiento.objects.prefetch_related('reabastecimientodetalle_set__producto').get(pk=pk)
        
        # New: Check if any lot associated with this restock has sales
        if Lote.objects.filter(reabastecimiento_detalle__reabastecimiento=reab, ventadetalle__isnull=False).exists():
            return JsonResponse({'error': 'No se puede editar, tiene productos vendidos.'}, status=400)
        
        if reab.estado == Reabastecimiento.ESTADO_RECIBIDO:
            return JsonResponse({'error': 'No se puede editar un reabastecimiento recibido.'}, status=400)

        data = {
            'id': reab.id, 'proveedor_id': reab.proveedor_id, 'fecha': reab.fecha.isoformat(),
            'forma_pago': reab.forma_pago, 'observaciones': reab.observaciones, 'estado': reab.estado,
            'iva': str(reab.iva),
            'detalles': [{
                'id': d.id, 'producto_id': d.producto_id, 'producto_nombre': d.producto.nombre,
                'cantidad': d.cantidad, 'cantidad_recibida': d.cantidad_recibida,
                'costo_unitario': str(d.costo_unitario),
                'iva': str(d.iva),
                'fecha_caducidad': d.fecha_caducidad.isoformat() if d.fecha_caducidad else None
            } for d in reab.reabastecimientodetalle_set.all()]
        }
        return JsonResponse(data)
    except Reabastecimiento.DoesNotExist:
        return JsonResponse({'error': 'Reabastecimiento no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@never_cache
@login_required
@check_user_role(allowed_roles=['Administrador'])
def reabastecimiento_update(request, pk):
    """Actualizar un reabastecimiento."""
    try:
        with transaction.atomic():
            reab = get_object_or_404(Reabastecimiento, pk=pk)
            if Lote.objects.filter(reabastecimiento_detalle__reabastecimiento=reab, ventadetalle__isnull=False).exists():
                return JsonResponse({'error': 'No se puede editar, tiene productos vendidos.'}, status=400)
            
            if reab.estado == Reabastecimiento.ESTADO_RECIBIDO:
                return JsonResponse({'error': 'No se puede editar un reabastecimiento recibido.'}, status=400)

            form = ReabastecimientoForm(request.POST, instance=reab)
            formset = ReabastecimientoDetalleFormSet(request.POST, instance=reab)

            if form.is_valid() and formset.is_valid():
                reab_instance = form.save(commit=False)
                
                total_costo = 0
                total_iva = 0
                
                # Guardar el formset para que se procesen los detalles
                detalles = formset.save(commit=False)

                for detalle in detalles:
                    # Calcular subtotal e iva para cada detalle
                    subtotal = detalle.cantidad * detalle.costo_unitario
                    tasa_iva_porcentaje = detalle.producto.tasa_iva.porcentaje
                    detalle.iva = subtotal * (tasa_iva_porcentaje / 100)
                    detalle.save()
                    
                    total_costo += subtotal
                    total_iva += detalle.iva

                # Procesar también los formularios que se van a eliminar
                for form_detalle in formset.deleted_forms:
                    # Si hay lógica adicional al eliminar, va aquí
                    pass

                reab_instance.costo_total = total_costo
                reab_instance.iva = total_iva
                reab_instance.save()

                if reab_instance.estado == Reabastecimiento.ESTADO_SOLICITADO:
                    send_supply_request_email(request, reab_instance)

                return JsonResponse({
                    'id': reab_instance.id,
                    'fecha': reab_instance.fecha.isoformat(),
                    'proveedor': reab_instance.proveedor.nombre_empresa,
                    'costo_total': float(reab_instance.costo_total),
                    'iva': float(reab_instance.iva),
                    'forma_pago': reab_instance.get_forma_pago_display(),
                    'estado': reab_instance.get_estado_display(),
                    'observaciones': reab_instance.observaciones,
                })
            else:
                return JsonResponse({'errors': form.errors, 'formset_errors': [f.errors for f in formset.forms if f.errors]}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@never_cache
@login_required
@check_user_role(allowed_roles=['Administrador'])
def reabastecimiento_recibir(request, pk):
    """Marcar un reabastecimiento como 'recibido' y crear lotes."""
    try:
        data = json.loads(request.body)
        with transaction.atomic():
            reab = get_object_or_404(Reabastecimiento, pk=pk)
            if reab.estado == Reabastecimiento.ESTADO_RECIBIDO:
                return JsonResponse({'error': 'Este reabastecimiento ya ha sido recibido.'}, status=400)

            productos_a_actualizar = set()
            discrepancias_productos = [] # List to store discrepancies

            for detalle_data in data.get('detalles', []):
                detalle = get_object_or_404(ReabastecimientoDetalle, pk=detalle_data.get('id'), reabastecimiento=reab)
                cantidad_recibida = int(detalle_data.get('cantidad_recibida'))
                fecha_caducidad_str = detalle_data.get('fecha_caducidad')

                if cantidad_recibida > detalle.cantidad:
                    raise ValueError(f'Cantidad recibida ({cantidad_recibida}) > solicitada ({detalle.cantidad}) para {detalle.producto.nombre}.')
                
                # Check for discrepancies
                if cantidad_recibida < detalle.cantidad:
                    discrepancias_productos.append({
                        'producto_nombre': detalle.producto.nombre,
                        'cantidad_solicitada': detalle.cantidad,
                        'cantidad_recibida': cantidad_recibida,
                    })

                detalle.cantidad_recibida = cantidad_recibida
                if fecha_caducidad_str:
                    detalle.fecha_caducidad = fecha_caducidad_str
                detalle.save()

                if cantidad_recibida > 0:
                    if not fecha_caducidad_str:
                        raise ValueError(f'Debe proporcionar una fecha de caducidad para {detalle.producto.nombre}.')

                    numero_lote = f"R{reab.pk}-P{detalle.producto.pk}-{detalle.pk}"
                    lote = Lote.objects.create(
                        producto=detalle.producto, reabastecimiento_detalle=detalle, numero_lote=numero_lote,
                        cantidad_disponible=cantidad_recibida, costo_unitario_lote=detalle.costo_unitario,
                        fecha_caducidad=fecha_caducidad_str
                    )
                    MovimientoInventario.objects.create(
                        producto=lote.producto, lote=lote, cantidad=cantidad_recibida, tipo_movimiento='entrada',
                        descripcion=f'Entrada por reabastecimiento #{reab.pk}', reabastecimiento_id=reab.pk
                    )
                    productos_a_actualizar.add(detalle.producto)

            # Check if there are discrepancies and send email
            if discrepancias_productos:
                send_discrepancy_email(reab, discrepancias_productos)

            reab.estado = Reabastecimiento.ESTADO_RECIBIDO
            reab.save()
            return JsonResponse({'message': 'Reabastecimiento recibido y stock actualizado.', 'estado': reab.get_estado_display()})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@never_cache
@login_required
@check_user_role(allowed_roles=['Administrador'])
def reabastecimiento_eliminar(request, pk):
    """Eliminar un reabastecimiento."""
    try:
        with transaction.atomic():
            reab = get_object_or_404(Reabastecimiento, pk=pk)
            if Lote.objects.filter(reabastecimiento_detalle__reabastecimiento=reab, ventadetalle__isnull=False).exists():
                return JsonResponse({'error': 'No se puede eliminar, tiene productos vendidos.'}, status=400)

            # Obtener los productos afectados ANTES de eliminar los lotes
            productos_a_actualizar = set(
                Producto.objects.filter(reabastecimientodetalle__reabastecimiento=reab)
            )

            Lote.objects.filter(reabastecimiento_detalle__reabastecimiento=reab).delete()
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM movimiento_inventario WHERE reabastecimiento_id = %s", [pk])
                cursor.execute("DELETE FROM reabastecimiento WHERE id = %s", [pk])

            # Actualizar los objetos Producto en Django para reflejar los cambios de la DB
            for producto in productos_a_actualizar:
                producto.refresh_from_db()

            return JsonResponse({'message': 'Reabastecimiento eliminado correctamente'})
    except Reabastecimiento.DoesNotExist:
        return JsonResponse({'error': 'Reabastecimiento no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# --- Vistas de Categoría y Producto (AJAX) ---

@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador'])
def categoria_create_ajax(request):
    """Crear una categoría vía AJAX."""
    try:
        data = json.loads(request.body)
        categoria, created = Categoria.objects.get_or_create(nombre=data.get('nombre'))
        return JsonResponse({'id': categoria.id, 'nombre': categoria.nombre})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador'])
def producto_create_ajax(request):
    """Crear un producto vía AJAX."""
    try:
        data = json.loads(request.body)
        form = ProductoForm(data)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.stock_actual = 0
            producto.costo_promedio = 0
            producto.save()
            return JsonResponse({
                'id': producto.id,
                'nombre': producto.nombre,
                'precio_unitario': float(producto.precio_unitario or 0)
            })
        else:
            errors = '<br>'.join([f'**{field}:** {error[0]}' for field, error in form.errors.items()])
            return JsonResponse({'message': f'Error de Validación<br>{errors}'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Error: Datos JSON inválidos.'}, status=400)
    except Exception as e:
        return JsonResponse({'message': f'Error inesperado: {str(e)}'}, status=500)
