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
from inventory.models import Producto, Categoria, Lote, MovimientoInventario
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
            nit=data['nit'],
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

    form = ReabastecimientoForm()
    formset = ReabastecimientoDetalleFormSet(queryset=ReabastecimientoDetalle.objects.none())

    productos_data = list(Producto.objects.values('id', 'precio_unitario'))
    all_products_data = list(Producto.objects.values('id', 'nombre'))
    categorias = Categoria.objects.all()

    context = {
        'reabastecimientos': reabs,
        'form': form,
        'formset': formset,
        'products_json': json.dumps(productos_data, cls=DjangoJSONEncoder),
        'all_products_json': json.dumps(all_products_data),
        'categorias': categorias,
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
                total = sum(
                    d['cantidad'] * float(d['costo_unitario'])
                    for d in formset.cleaned_data if d and not d.get('DELETE')
                )
                if total == 0:
                    return JsonResponse({'error': 'Debe agregar al menos un detalle de producto.'}, status=400)

                reab.costo_total = total
                reab.save()

                detalles_data = []
                for detalle_form in formset.cleaned_data:
                    if detalle_form and not detalle_form.get('DELETE'):
                        # Eliminar 'reabastecimiento' si existe para evitar el error de argumento múltiple
                        detalle_form.pop('reabastecimiento', None)
                        # Eliminar 'DELETE' para que no se pase al crear el objeto
                        detalle_form.pop('DELETE', None)
                        detalle = ReabastecimientoDetalle.objects.create(reabastecimiento=reab, **detalle_form)
                        detalles_data.append({
                            'producto_nombre': detalle.producto.nombre,
                            'categoria_nombre': detalle.producto.categoria.nombre,
                            'cantidad': detalle.cantidad,
                            'costo_unitario': float(detalle.costo_unitario),
                            'subtotal': float(detalle.cantidad * detalle.costo_unitario),
                            'estado_lote': 'No recibido'
                        })

                if reab.estado == Reabastecimiento.ESTADO_SOLICITADO:
                    send_supply_request_email(request, reab)

                return JsonResponse({
                    'id': reab.id, 'fecha': reab.fecha.isoformat(),
                    'proveedor': reab.proveedor.nombre_empresa, 'costo_total': float(reab.costo_total),
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
        if reab.estado == Reabastecimiento.ESTADO_RECIBIDO:
            return JsonResponse({'error': 'No se puede editar un reabastecimiento recibido.'}, status=400)

        data = {
            'id': reab.id, 'proveedor_id': reab.proveedor_id, 'fecha': reab.fecha.isoformat(),
            'forma_pago': reab.forma_pago, 'observaciones': reab.observaciones, 'estado': reab.estado,
            'detalles': [{
                'id': d.id, 'producto_id': d.producto_id, 'producto_nombre': d.producto.nombre,
                'cantidad': d.cantidad, 'cantidad_recibida': d.cantidad_recibida,
                'costo_unitario': str(d.costo_unitario),
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
@require_POST
@check_user_role(allowed_roles=['Administrador'])
def reabastecimiento_update(request, pk):
    """Actualizar un reabastecimiento."""
    try:
        with transaction.atomic():
            reab = get_object_or_404(Reabastecimiento, pk=pk)
            if reab.estado == Reabastecimiento.ESTADO_RECIBIDO:
                return JsonResponse({'error': 'No se puede editar un reabastecimiento recibido.'}, status=400)

            form = ReabastecimientoForm(request.POST, instance=reab)
            formset = ReabastecimientoDetalleFormSet(request.POST, instance=reab)

            if form.is_valid() and formset.is_valid():
                reab_instance = form.save()
                formset.save()

                total = sum(
                    d.cleaned_data['cantidad'] * float(d.cleaned_data['costo_unitario'])
                    for d in formset.forms if d.cleaned_data and not d.cleaned_data.get('DELETE')
                )
                reab_instance.costo_total = total
                reab_instance.save()

                if reab_instance.estado == Reabastecimiento.ESTADO_SOLICITADO:
                    send_supply_request_email(request, reab_instance)

                return JsonResponse({
                    'id': reab_instance.id, 'fecha': reab_instance.fecha.isoformat(),
                    'proveedor': reab_instance.proveedor.nombre_empresa, 'costo_total': float(reab_instance.costo_total),
                    'forma_pago': reab_instance.get_forma_pago_display(), 'estado': reab_instance.get_estado_display(),
                    'observaciones': reab_instance.observaciones,
                })
            else:
                return JsonResponse({'errors': form.errors, 'formset_errors': [f.errors for f in formset.forms if f.errors]}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@never_cache
@login_required
@require_POST
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

            for detalle_data in data.get('detalles', []):
                detalle = get_object_or_404(ReabastecimientoDetalle, pk=detalle_data.get('id'), reabastecimiento=reab)
                cantidad_recibida = int(detalle_data.get('cantidad_recibida'))
                fecha_caducidad_str = detalle_data.get('fecha_caducidad')

                if cantidad_recibida > detalle.cantidad:
                    raise ValueError(f'Cantidad recibida ({cantidad_recibida}) > solicitada ({detalle.cantidad}) para {detalle.producto.nombre}.')

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

            for producto in productos_a_actualizar:
                producto.refresh_from_db()

            reab.estado = Reabastecimiento.ESTADO_RECIBIDO
            reab.save()
            return JsonResponse({'message': 'Reabastecimiento recibido y stock actualizado.', 'estado': reab.get_estado_display()})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@never_cache
@login_required
@require_POST
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