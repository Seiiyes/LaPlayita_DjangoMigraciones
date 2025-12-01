from django.shortcuts import render, get_object_or_404, redirect
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
from django.urls import reverse # Added import for reverse
import logging

from django.db.models import Q, Sum # Added for OR queries
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from users.decorators import check_user_role
from .models import Proveedor, Reabastecimiento, ReabastecimientoDetalle
from inventory.models import Producto, Categoria, Lote, MovimientoInventario, TasaIVA
from inventory.forms import ReabastecimientoForm, ReabastecimientoDetalleFormSet, ProductoForm
from suppliers.forms import ReabastecimientoDetalleFormSetEdit

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

logger = logging.getLogger(__name__)

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

@login_required
def search_suppliers_ajax(request):
    """
    AJAX view to search for suppliers by name or ID for Select2.
    """
    query = request.GET.get('q', '')
    if query:
        suppliers = Proveedor.objects.filter(
            Q(nombre_empresa__icontains=query) |
            Q(documento_identificacion__icontains=query)
        ).values('id', 'nombre_empresa')
        results = [{'id': s['id'], 'text': s['nombre_empresa']} for s in suppliers]
    else:
        results = []
    return JsonResponse({'results': results})

@login_required
def search_products_ajax(request):
    """
    AJAX view to search for products by name for Select2.
    """
    query = request.GET.get('q', '')
    if query:
        products = Producto.objects.filter(nombre__icontains=query).values('id', 'nombre')
        results = [{'id': p['id'], 'text': p['nombre']} for p in products]
    else:
        results = []
    return JsonResponse({'results': results})


# --- Vistas de Reabastecimientos ---

def send_supply_request_email(reabastecimiento, request=None):
    """
    Envía un correo al proveedor notificando sobre una nueva solicitud de reabastecimiento.
    """
    logger.info(f"[EMAIL] Iniciando envío de correo para reabastecimiento {reabastecimiento.id}")
    
    try:
        proveedor = reabastecimiento.proveedor
        if not proveedor or not proveedor.correo:
            logger.warning(f"[EMAIL] Proveedor {proveedor.nombre_empresa if proveedor else 'N/A'} sin correo. No se puede enviar la solicitud.")
            return False

        subject = f'Solicitud de Reabastecimiento #{reabastecimiento.id}'
        
        # Contexto para la plantilla
        context = {
            'reabastecimiento': reabastecimiento,
            'proveedor_nombre': proveedor.nombre_empresa,
            'current_year': datetime.now().year,
        }
        
        # Renderizar plantilla HTML
        html_content = render_to_string('suppliers/emails/reabastecimiento_solicitud.html', context)
        
        # Crear contenido de texto simple como alternativa
        text_content = f"Estimado/a {proveedor.nombre_empresa},\n\n"
        text_content += "Se ha generado una nueva solicitud de reabastecimiento por parte de La Playita.\n\n"
        text_content += f"ID de Reabastecimiento: {reabastecimiento.id}\n"
        text_content += f"Fecha de Solicitud: {reabastecimiento.fecha.strftime('%d/%m/%Y %H:%M')}\n"
        text_content += f"Observaciones: {reabastecimiento.observaciones or 'N/A'}\n\n"
        text_content += "Productos solicitados:\n"
        
        detalles = reabastecimiento.reabastecimientodetalle_set.all()
        if detalles:
            for detalle in detalles:
                text_content += f"- {detalle.producto.nombre}: {detalle.cantidad} unidades\n"
        else:
            text_content += "(No se especificaron productos)\n"
            
        text_content += "\nAgradecemos su pronta atención a esta solicitud.\n\n"
        text_content += "Saludos cordiales,\nEl equipo de La Playita"

        # Crear el correo
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            to=[proveedor.correo]
        )
        email.attach_alternative(html_content, "text/html")

        # Adjuntar el logo
        try:
            logo_path = find_static('core/img/la-playita-logo.png')
            if logo_path:
                with open(logo_path, 'rb') as f:
                    logo_data = f.read()
                logo_mime = MIMEImage(logo_data)
                logo_mime.add_header('Content-ID', '<logo>')
                email.attach(logo_mime)
                logger.info("[EMAIL] Logo adjuntado correctamente.")
            else:
                logger.warning("[EMAIL] No se encontró el archivo del logo.")
        except Exception as logo_error:
            logger.error(f"[EMAIL] Error al adjuntar el logo: {logo_error}", exc_info=True)

        # Enviar correo
        email.send(fail_silently=False)
        
        logger.info(f"[EMAIL] ✓ Correo para reabastecimiento {reabastecimiento.id} enviado exitosamente a {proveedor.correo}")
        return True

    except Exception as e:
        logger.error(f"[EMAIL] ✗ Error al enviar correo para reabastecimiento {reabastecimiento.id}: {e}", exc_info=True)
        return False


def send_discrepancy_email(reabastecimiento, discrepancias):
    """
    Envía un correo al proveedor notificando sobre una discrepancia en un reabastecimiento.
    """
    logger.info(f"[EMAIL] Iniciando envío de correo de discrepancia para reabastecimiento {reabastecimiento.id}")
    
    try:
        proveedor = reabastecimiento.proveedor
        if not proveedor or not proveedor.correo:
            logger.warning(f"[EMAIL] Proveedor {proveedor.nombre_empresa if proveedor else 'N/A'} sin correo. No se puede enviar el correo de discrepancia.")
            return False

        subject = f'Discrepancia en Reabastecimiento #{reabastecimiento.id}'
        
        # Contexto para la plantilla
        context = {
            'reabastecimiento': reabastecimiento,
            'discrepancias': discrepancias,
            'current_year': datetime.now().year,
        }
        
        # Renderizar plantilla HTML
        html_content = render_to_string('suppliers/emails/reabastecimiento_discrepancia.html', context)
        
        # Crear contenido de texto simple como alternativa
        text_content = f"Estimado/a {proveedor.nombre_empresa},\n\n"
        text_content += f"Se ha detectado una discrepancia en la recepción del Reabastecimiento #{reabastecimiento.id}.\n\n"
        text_content += "Los siguientes productos presentan diferencias:\n"
        
        for disc in discrepancias:
            text_content += f"- Producto: {disc['producto_nombre']}\n"
            text_content += f"  Cantidad Solicitada: {disc['cantidad_solicitada']}\n"
            text_content += f"  Cantidad Recibida: {disc['cantidad_recibida']}\n\n"

        text_content += "Por favor, revise los detalles y tome las acciones correspondientes.\n\n"
        text_content += "Saludos cordiales,\nEl equipo de La Playita"

        # Crear el correo
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            to=[proveedor.correo]
        )
        email.attach_alternative(html_content, "text/html")

        # Adjuntar el logo
        try:
            logo_path = find_static('core/img/la-playita-logo.png')
            if logo_path:
                with open(logo_path, 'rb') as f:
                    logo_data = f.read()
                logo_mime = MIMEImage(logo_data)
                logo_mime.add_header('Content-ID', '<logo>')
                email.attach(logo_mime)
                logger.info("[EMAIL] Logo adjuntado correctamente al correo de discrepancia.")
            else:
                logger.warning("[EMAIL] No se encontró el archivo del logo para el correo de discrepancia.")
        except Exception as logo_error:
            logger.error(f"[EMAIL] Error al adjuntar el logo al correo de discrepancia: {logo_error}", exc_info=True)

        # Enviar correo
        email.send(fail_silently=False)
        
        logger.info(f"[EMAIL] ✓ Correo de discrepancia para reabastecimiento {reabastecimiento.id} enviado exitosamente a {proveedor.correo}")
        return True

    except Exception as e:
        logger.error(f"[EMAIL] ✗ Error al enviar correo de discrepancia para reabastecimiento {reabastecimiento.id}: {e}", exc_info=True)
        return False


# --- Vistas de Reabastecimientos ---

@never_cache
@login_required
@check_user_role(allowed_roles=['Administrador'])
def reabastecimiento_list(request):
    """
    Lista los reabastecimientos con filtrado y búsqueda.
    """
    reabs_query = (
        Reabastecimiento.objects
        .select_related('proveedor')
        .prefetch_related(
            'reabastecimientodetalle_set__producto__categoria',
            'reabastecimientodetalle_set__lote_set__ventadetalle_set'
        )
        .order_by('-fecha')
    )

    # Filtering logic
    q = request.GET.get('q')
    proveedor_id = request.GET.get('proveedor_id')
    producto_id = request.GET.get('producto_id')
    estado = request.GET.get('estado')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if q:
        if q.isdigit():
            reabs_query = reabs_query.filter(Q(id=q) | Q(proveedor__nombre_empresa__icontains=q) | Q(reabastecimientodetalle__producto__nombre__icontains=q)).distinct()
        else:
            reabs_query = reabs_query.filter(Q(proveedor__nombre_empresa__icontains=q) | Q(reabastecimientodetalle__producto__nombre__icontains=q)).distinct()

    if proveedor_id:
        reabs_query = reabs_query.filter(proveedor_id=proveedor_id)
    
    if producto_id:
        reabs_query = reabs_query.filter(reabastecimientodetalle__producto_id=producto_id).distinct()

    if estado:
        reabs_query = reabs_query.filter(estado=estado)
    else:
        reabs_query = reabs_query.exclude(estado=Reabastecimiento.ESTADO_CANCELADO)

    if fecha_desde:
        reabs_query = reabs_query.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        end_of_day = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        reabs_query = reabs_query.filter(fecha__lte=end_of_day)
    
    # Apply pagination
    paginator = Paginator(reabs_query.all(), 10)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    for reab in page_obj.object_list:
        reab.tiene_ventas = any(
            lote.ventadetalle_set.exists()
            for detalle in reab.reabastecimientodetalle_set.all()
            for lote in detalle.lote_set.all()
        )

    # Prepare initial values for Select2 in template
    proveedor_text = ''
    if proveedor_id:
        try:
            proveedor = Proveedor.objects.get(id=proveedor_id)
            proveedor_text = proveedor.nombre_empresa
        except Proveedor.DoesNotExist:
            pass

    producto_text = ''
    if producto_id:
        try:
            producto = Producto.objects.get(id=producto_id)
            producto_text = producto.nombre
        except Producto.DoesNotExist:
            pass
            
    context = {
        'reabastecimientos': page_obj.object_list,
        'page_obj': page_obj,
        'proveedor_id_selected': proveedor_id,
        'proveedor_text_selected': proveedor_text,
        'producto_id_selected': producto_id,
        'producto_text_selected': producto_text,
    }
    return render(request, 'suppliers/reabastecimiento_list.html', context)

@never_cache
@login_required
@check_user_role(allowed_roles=['Administrador'])
def reabastecimiento_create(request):
    """
    Crear un reabastecimiento con múltiples detalles en una página dedicada.
    Optimizado para velocidad y cero fricción.
    """
    if request.method == 'POST':
        form = ReabastecimientoForm(request.POST)
        formset = ReabastecimientoDetalleFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    logger.info("[REAB] Iniciando creación de reabastecimiento")
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
                            
                            # Usar el IVA del formulario, que ahora se calcula en el frontend
                            iva_detalle = detalle_form.get('iva', 0)
                            if iva_detalle is None:
                                # Fallback por si el frontend no envía el IVA
                                iva_porcentaje = producto.tasa_iva.porcentaje if producto.tasa_iva else 0
                                iva_detalle = subtotal * (iva_porcentaje / 100)
                            
                            total_costo += subtotal
                            total_iva += iva_detalle
                            # El valor de 'iva' ya está en detalle_form, no es necesario reasignarlo
                            detalles_a_crear.append(detalle_form)

                    if not detalles_a_crear:
                        form.add_error(None, "Agrega al menos un producto")
                        raise ValueError("No hay detalles para crear")

                    reab.costo_total = total_costo
                    reab.iva = total_iva
                    reab.save()
                    logger.info(f"[REAB] Reabastecimiento guardado: ID {reab.id}")

                    for detalle_form_data in detalles_a_crear:
                        # Eliminar campos que no pertenecen al modelo
                        detalle_form_data.pop('DELETE', None)
                        detalle_form_data.pop('reabastecimiento', None)
                        detalle_form_data.pop('iva_porcentaje', None)
                        ReabastecimientoDetalle.objects.create(reabastecimiento=reab, **detalle_form_data)
                    logger.info(f"[REAB] Detalles guardados: {len(detalles_a_crear)}")

                    if reab.estado == Reabastecimiento.ESTADO_SOLICITADO:
                        logger.info(f"[REAB] Enviando correo para reabastecimiento {reab.id}")
                        try:
                            send_supply_request_email(reab, request)
                        except Exception as email_error:
                            logger.error(f"[REAB] Error al enviar correo: {email_error}", exc_info=True)
                    
                    logger.info("[REAB] Reabastecimiento creado exitosamente")
                    return redirect('suppliers:reabastecimiento_list')

            except Exception as e:
                logger.error(f"[REAB] Error al crear reabastecimiento: {e}", exc_info=True)
                form.add_error(None, f"Error inesperado: {e}")
        
    else:
        form = ReabastecimientoForm(initial_creation=True)
        formset = ReabastecimientoDetalleFormSet(queryset=ReabastecimientoDetalle.objects.none())

    all_products_data = list(Producto.objects.values('id', 'nombre', 'precio_unitario', 'tasa_iva_id', 'tasa_iva__porcentaje'))
    recent_suppliers = Proveedor.objects.filter(
        reabastecimiento__isnull=False
    ).distinct().order_by('-reabastecimiento__fecha')[:5]
    
    # Obtener todas las tasas de IVA de la base de datos
    tasas_iva_queryset = TasaIVA.objects.all().order_by('porcentaje')
    tasas_iva_list = [{'id': t.id, 'porcentaje': float(t.porcentaje), 'nombre': t.nombre} for t in tasas_iva_queryset]
    
    context = {
        'form': form,
        'formset': formset,
        'all_products_json': json.dumps(all_products_data, cls=DjangoJSONEncoder),
        'tasas_iva_json': json.dumps(tasas_iva_list, cls=DjangoJSONEncoder),
        'recent_suppliers': recent_suppliers,
        'search_suppliers_url': reverse('suppliers:search_suppliers_ajax'),
        'search_products_url': reverse('suppliers:search_products_ajax'),
    }
    return render(request, 'suppliers/reabastecimiento_create.html', context)




@never_cache
@login_required
@check_user_role(allowed_roles=['Administrador'])
def reabastecimiento_editar(request, pk):
    """Vista para renderizar la página de edición de un reabastecimiento."""
    try:
        reab = Reabastecimiento.objects.prefetch_related('reabastecimientodetalle_set__producto__tasa_iva').get(pk=pk)
        
        # Check if any lot associated with this restock has sales
        if Lote.objects.filter(reabastecimiento_detalle__reabastecimiento=reab, ventadetalle__isnull=False).exists():
            return render(request, 'suppliers/error.html', {'error': 'No se puede editar, tiene productos vendidos.'}, status=400)
        
        if reab.estado == Reabastecimiento.ESTADO_RECIBIDO:
            return render(request, 'suppliers/error.html', {'error': 'No se puede editar un reabastecimiento recibido.'}, status=400)

        # Debug: Verificar IVA guardado en BD
        logger.info(f"[EDITAR] Reabastecimiento {pk}: IVA total = {reab.iva}")
        for detalle in reab.reabastecimientodetalle_set.all():
            logger.info(f"[EDITAR] Detalle {detalle.id}: producto={detalle.producto.nombre}, iva={detalle.iva}, cantidad={detalle.cantidad}, costo={detalle.costo_unitario}")
        
        form = ReabastecimientoForm(instance=reab)
        formset = ReabastecimientoDetalleFormSetEdit(instance=reab)
        
        all_products_data = list(Producto.objects.values('id', 'nombre', 'precio_unitario', 'tasa_iva_id', 'tasa_iva__porcentaje'))
        tasas_iva_queryset = TasaIVA.objects.all().order_by('porcentaje')
        tasas_iva_list = [{'id': t.id, 'porcentaje': float(t.porcentaje), 'nombre': t.nombre} for t in tasas_iva_queryset]
        
        context = {
            'reabastecimiento': reab,
            'form': form,
            'formset': formset,
            'all_products_json': json.dumps(all_products_data, cls=DjangoJSONEncoder),
            'tasas_iva_json': json.dumps(tasas_iva_list, cls=DjangoJSONEncoder),
        }
        return render(request, 'suppliers/reabastecimiento_editar.html', context)
    except Reabastecimiento.DoesNotExist:
        return render(request, 'suppliers/error.html', {'error': 'Reabastecimiento no encontrado'}, status=404)
    except Exception as e:
        return render(request, 'suppliers/error.html', {'error': str(e)}, status=500)

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
            formset = ReabastecimientoDetalleFormSetEdit(request.POST, instance=reab)
            
            logger.info(f"[UPDATE] Form valid: {form.is_valid()}, Formset valid: {formset.is_valid()}")
            if not form.is_valid():
                logger.error(f"[UPDATE] Form errors: {form.errors}")
            if not formset.is_valid():
                logger.error(f"[UPDATE] Formset errors: {formset.errors}")
                for idx, f in enumerate(formset.forms):
                    if f.errors:
                        logger.error(f"[UPDATE] Form {idx} errors: {f.errors}")

            if form.is_valid() and formset.is_valid():
                from decimal import Decimal
                
                reab_instance = form.save(commit=False)
                
                total_costo = Decimal('0')
                total_iva = Decimal('0')
                
                logger.info(f"[UPDATE] Procesando {len(formset.forms)} detalles")
                
                # Procesar los detalles
                for idx, detalle_form in enumerate(formset.forms):
                    logger.info(f"[UPDATE] Detalle {idx}: cleaned_data={detalle_form.cleaned_data}, DELETE={detalle_form.cleaned_data.get('DELETE') if detalle_form.cleaned_data else 'N/A'}")
                    
                    if detalle_form.cleaned_data and not detalle_form.cleaned_data.get('DELETE'):
                        detalle = detalle_form.save(commit=False)
                        
                        # Calcular subtotal
                        subtotal = detalle.cantidad * detalle.costo_unitario
                        
                        # Obtener el IVA del formulario
                        iva_valor = detalle_form.cleaned_data.get('iva')
                        
                        logger.info(f"[UPDATE] Detalle {idx}: iva_valor={iva_valor}, subtotal={subtotal}")
                        
                        # Usar el IVA del formulario si está presente (incluso si es 0)
                        if iva_valor is not None:
                            # El IVA viene del formulario, usarlo tal cual
                            iva_detalle = Decimal(str(iva_valor))
                            logger.info(f"[UPDATE] Detalle {idx}: Usando IVA del formulario: {iva_detalle}")
                        else:
                            # Calcular IVA basado en el porcentaje del producto
                            if detalle.producto and detalle.producto.tasa_iva:
                                tasa_iva_porcentaje = Decimal(str(detalle.producto.tasa_iva.porcentaje))
                                iva_detalle = subtotal * (tasa_iva_porcentaje / Decimal('100'))
                                logger.info(f"[UPDATE] Detalle {idx}: Calculando IVA: {iva_detalle}")
                            else:
                                iva_detalle = Decimal('0')
                                logger.info(f"[UPDATE] Detalle {idx}: Sin tasa IVA, IVA=0")
                        
                        detalle.iva = iva_detalle
                        detalle.fecha_caducidad = detalle_form.cleaned_data.get('fecha_caducidad')
                        logger.info(f"[UPDATE] Detalle {idx}: Guardando - iva={detalle.iva}, fecha_caducidad={detalle.fecha_caducidad}")
                        detalle.save()
                        
                        total_costo += subtotal
                        total_iva += iva_detalle
                    elif detalle_form.cleaned_data and detalle_form.cleaned_data.get('DELETE'):
                        # Eliminar el detalle
                        if detalle_form.instance.pk:
                            logger.info(f"[UPDATE] Detalle {idx}: Eliminando detalle {detalle_form.instance.pk}")
                            detalle_form.instance.delete()
                
                logger.info(f"[UPDATE] Totales finales: costo_total={total_costo}, iva={total_iva}")
                
                reab_instance.costo_total = total_costo
                reab_instance.iva = total_iva
                reab_instance.save()
                
                logger.info(f"[UPDATE] Reabastecimiento {reab_instance.id} guardado exitosamente")

                if reab_instance.estado == Reabastecimiento.ESTADO_SOLICITADO:
                    send_supply_request_email(reab_instance, request)

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
    """Marcar un reabastecimiento como 'recibido' y crear lotes con auditoría automática."""
    try:
        from .models import AuditoriaReabastecimiento
        
        print(f"DEBUG: Iniciando recepción para reabastecimiento {pk}")
        data = json.loads(request.body)
        print(f"DEBUG: Datos recibidos: {data}")
        with transaction.atomic():
            reab = get_object_or_404(Reabastecimiento, pk=pk)
            if reab.estado == Reabastecimiento.ESTADO_RECIBIDO:
                return JsonResponse({'error': 'Este reabastecimiento ya ha sido recibido.'}, status=400)

            productos_a_actualizar = set()
            discrepancias_productos = []
            detalles_recibidos = []

            for detalle_data in data.get('detalles', []):
                detalle = get_object_or_404(ReabastecimientoDetalle, pk=detalle_data.get('id'), reabastecimiento=reab)
                cantidad_recibida = int(detalle_data.get('cantidad_recibida'))
                fecha_caducidad_str = detalle_data.get('fecha_caducidad')
                numero_lote = detalle_data.get('numero_lote', '')

                if cantidad_recibida > detalle.cantidad:
                    raise ValueError(f'Cantidad recibida ({cantidad_recibida}) > solicitada ({detalle.cantidad}) para {detalle.producto.nombre}.')
                
                # Registrar discrepancias
                if cantidad_recibida < detalle.cantidad and cantidad_recibida > 0:
                    discrepancias_productos.append({
                        'producto_nombre': detalle.producto.nombre,
                        'cantidad_solicitada': detalle.cantidad,
                        'cantidad_recibida': cantidad_recibida,
                    })

                # Guardar cantidad anterior para auditoría
                cantidad_anterior = detalle.cantidad_recibida

                # Actualizar detalle
                detalle.cantidad_recibida = cantidad_recibida
                if fecha_caducidad_str:
                    detalle.fecha_caducidad = fecha_caducidad_str
                if numero_lote:
                    detalle.numero_lote = numero_lote
                detalle.recibido_por = request.user
                detalle.fecha_recepcion = timezone.now()
                
                print(f"DEBUG: Guardando detalle {detalle.id}")
                print(f"  cantidad_recibida antes de save: {detalle.cantidad_recibida}")
                detalle.save()
                print(f"  cantidad_recibida después de save: {detalle.cantidad_recibida}")
                
                # Verificar que se guardó correctamente
                detalle.refresh_from_db()
                print(f"  cantidad_recibida después de refresh: {detalle.cantidad_recibida}")

                if cantidad_recibida > 0:
                    if not fecha_caducidad_str:
                        raise ValueError(f'Debe proporcionar una fecha de caducidad para {detalle.producto.nombre}.')

                    # Generar número de lote si no se proporciona
                    if not numero_lote:
                        numero_lote = f"R{reab.pk}-P{detalle.producto.pk}-{detalle.pk}"
                    
                    lote = Lote.objects.create(
                        producto=detalle.producto, 
                        reabastecimiento_detalle=detalle, 
                        numero_lote=numero_lote,
                        cantidad_disponible=cantidad_recibida,
                        costo_unitario_lote=detalle.costo_unitario,
                        fecha_caducidad=fecha_caducidad_str
                    )
                    MovimientoInventario.objects.create(
                        producto=lote.producto, 
                        lote=lote, 
                        cantidad=cantidad_recibida, 
                        tipo_movimiento='entrada',
                        descripcion=f'Entrada por reabastecimiento #{reab.pk}', 
                        reabastecimiento_id=reab.pk
                    )
                    productos_a_actualizar.add(detalle.producto)
                    
                    detalles_recibidos.append({
                        'producto': detalle.producto.nombre,
                        'cantidad': cantidad_recibida,
                        'lote': numero_lote
                    })

            # Registrar auditoría de recepción
            descripcion_auditoria = f"Recepción completada: {len(detalles_recibidos)} productos recibidos"
            if discrepancias_productos:
                descripcion_auditoria += f", {len(discrepancias_productos)} con discrepancias"
            
            AuditoriaReabastecimiento.objects.create(
                reabastecimiento=reab,
                usuario=request.user,
                accion='recibido',
                descripcion=descripcion_auditoria,
                cantidad_nueva=sum(d['cantidad'] for d in detalles_recibidos)
            )

            # Cambiar estado
            reab.estado = Reabastecimiento.ESTADO_RECIBIDO
            reab.save()

            # Enviar email de discrepancias si las hay
            if discrepancias_productos:
                send_discrepancy_email(reab, discrepancias_productos)

            return JsonResponse({
                'message': 'Reabastecimiento recibido y stock actualizado.',
                'estado': reab.get_estado_display(),
                'detalles_recibidos': len(detalles_recibidos),
                'discrepancias': len(discrepancias_productos)
            })
    except Exception as e:
        print(f"DEBUG: Error en reabastecimiento_recibir: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@never_cache
@login_required
@check_user_role(allowed_roles=['Administrador'])
def reabastecimiento_update_received(request, pk):
    """Permitir edición limitada post-recepción (solo fecha y lote)."""
    try:
        from .models import AuditoriaReabastecimiento
        
        data = json.loads(request.body)
        with transaction.atomic():
            reab = get_object_or_404(Reabastecimiento, pk=pk)
            
            if reab.estado != Reabastecimiento.ESTADO_RECIBIDO:
                return JsonResponse({'error': 'Solo se puede editar recepciones completadas'}, status=400)

            cambios_realizados = []

            for detalle_data in data.get('detalles', []):
                detalle = get_object_or_404(ReabastecimientoDetalle, pk=detalle_data.get('id'), reabastecimiento=reab)
                
                # Solo permitir cambios en fecha_caducidad y numero_lote
                nueva_fecha = detalle_data.get('fecha_caducidad')
                nuevo_lote = detalle_data.get('numero_lote')
                
                cambio = False
                
                if nueva_fecha and detalle.fecha_caducidad != nueva_fecha:
                    detalle.fecha_caducidad = nueva_fecha
                    cambio = True
                    cambios_realizados.append(f"{detalle.producto.nombre}: fecha actualizada")
                
                if nuevo_lote and detalle.numero_lote != nuevo_lote:
                    detalle.numero_lote = nuevo_lote
                    cambio = True
                    cambios_realizados.append(f"{detalle.producto.nombre}: lote actualizado")
                
                if cambio:
                    detalle.save()

            # Registrar auditoría de cambios post-recepción
            if cambios_realizados:
                AuditoriaReabastecimiento.objects.create(
                    reabastecimiento=reab,
                    usuario=request.user,
                    accion='editado',
                    descripcion=f"Actualización post-recepción: {', '.join(cambios_realizados)}"
                )

            return JsonResponse({
                'message': 'Cambios guardados correctamente',
                'cambios': len(cambios_realizados)
            })
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

@login_required
@check_user_role(allowed_roles=['Administrador'])
def reabastecimiento_audit_history(request, pk):
    """Obtener historial de auditoría de un reabastecimiento."""
    try:
        from .models import AuditoriaReabastecimiento
        
        reab = get_object_or_404(Reabastecimiento, pk=pk)
        auditorias = AuditoriaReabastecimiento.objects.filter(
            reabastecimiento=reab
        ).select_related('usuario').order_by('-fecha')
        
        data = {
            'reabastecimiento_id': reab.id,
            'auditorias': [{
                'id': a.id,
                'accion': a.get_accion_display(),
                'usuario': a.usuario.get_full_name() if a.usuario else 'Sistema',
                'fecha': a.fecha.isoformat(),
                'descripcion': a.descripcion,
                'cantidad_anterior': a.cantidad_anterior,
                'cantidad_nueva': a.cantidad_nueva
            } for a in auditorias]
        }
        return JsonResponse(data)
    except Reabastecimiento.DoesNotExist:
        return JsonResponse({'error': 'Reabastecimiento no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@check_user_role(allowed_roles=['Administrador'])
def reabastecimiento_row_api(request, pk):
    """
    API endpoint to fetch a single Reabastecimiento row and render a partial HTML.
    Used for dynamic updates of the master list.
    """
    try:
        reabastecimiento = get_object_or_404(
            Reabastecimiento.objects.select_related('proveedor').prefetch_related(
                'reabastecimientodetalle_set__producto__categoria',
                'reabastecimientodetalle_set__lote_set__ventadetalle_set'
            ), pk=pk
        )
        reabastecimiento.tiene_ventas = any(
            lote.ventadetalle_set.exists()
            for detalle in reabastecimiento.reabastecimientodetalle_set.all()
            for lote in detalle.lote_set.all()
        )
        context = {
            'r': reabastecimiento, # Use 'r' to match existing template loop variable
        }
        html_content = render_to_string('suppliers/partials/reabastecimiento_row.html', context, request=request)
        return JsonResponse({'html': html_content})
    except Reabastecimiento.DoesNotExist:
        return JsonResponse({'error': 'Reabastecimiento no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# --- New API Endpoints for Reabastecimiento ---

@never_cache
@login_required
@check_user_role(allowed_roles=['Administrador'])
def reabastecimiento_detail_api(request, pk):
    """
    API endpoint to fetch details of a single Reabastecimiento as JSON for reception mode.
    Returns JSON with reabastecimiento data and detalles array.
    """
    try:
        reabastecimiento = get_object_or_404(
            Reabastecimiento.objects.select_related('proveedor').prefetch_related(
                'reabastecimientodetalle_set__producto'
            ), 
            pk=pk
        )
        
        # Build detalles array using ORM
        detalles = []
        iva_porcentaje_total = 0
        for detalle in reabastecimiento.reabastecimientodetalle_set.all():
            # Calcular el porcentaje de IVA
            subtotal = float(detalle.cantidad or 0) * float(detalle.costo_unitario or 0)
            iva_porcentaje = 0
            if subtotal > 0:
                iva_porcentaje = (float(detalle.iva or 0) / subtotal) * 100
            
            detalles.append({
                'id': detalle.id,
                'cantidad': int(detalle.cantidad or 0),
                'cantidad_recibida': int(detalle.cantidad_recibida or 0),
                'costo_unitario': float(detalle.costo_unitario or 0),
                'iva': float(detalle.iva or 0),
                'iva_porcentaje': round(iva_porcentaje, 2),
                'fecha_caducidad': detalle.fecha_caducidad.isoformat() if detalle.fecha_caducidad else '',
                'numero_lote': detalle.numero_lote or '',
                'producto_nombre': detalle.producto.nombre if detalle.producto else 'Producto desconocido',
            })
        
        # Calcular el porcentaje de IVA total
        iva_porcentaje_total = 0
        if float(reabastecimiento.costo_total or 0) > 0:
            iva_porcentaje_total = (float(reabastecimiento.iva or 0) / float(reabastecimiento.costo_total or 0)) * 100
        
        data = {
            'id': reabastecimiento.id,
            'proveedor_nombre': reabastecimiento.proveedor.nombre_empresa if reabastecimiento.proveedor else 'N/A',
            'proveedor_id': reabastecimiento.proveedor.id if reabastecimiento.proveedor else None,
            'fecha': reabastecimiento.fecha.isoformat() if reabastecimiento.fecha else None,
            'estado': reabastecimiento.estado,
            'forma_pago': reabastecimiento.forma_pago or '',
            'observaciones': reabastecimiento.observaciones or '',
            'costo_total': float(reabastecimiento.costo_total or 0),
            'iva': float(reabastecimiento.iva or 0),
            'iva_porcentaje': round(iva_porcentaje_total, 2),
            'detalles': detalles,
            'total_detalles': len(detalles),
        }
        return JsonResponse(data)
    except Reabastecimiento.DoesNotExist:
        return JsonResponse({'error': 'Reabastecimiento no encontrado'}, status=404)
    except Exception as e:
        print(f"Error en reabastecimiento_detail_api: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@check_user_role(allowed_roles=['Administrador'])
def get_reception_form_api(request, pk):
    """
    API endpoint to fetch the reception formset for a Reabastecimiento and render partial HTML.
    """
    try:
        reabastecimiento = get_object_or_404(
            Reabastecimiento.objects.prefetch_related(
                'reabastecimientodetalle_set__producto',
                'reabastecimientodetalle_set__lote_set'
            ), pk=pk
        )
        
        # You might want to filter details that haven't been fully received yet
        detalles = reabastecimiento.reabastecimientodetalle_set.all().order_by('producto__nombre')
        
        context = {
            'reabastecimiento': reabastecimiento,
            'detalles': detalles,
        }
        html_content = render_to_string('suppliers/partials/reabastecimiento_reception_formset.html', context, request=request)
        return JsonResponse({'html': html_content})
    except Reabastecimiento.DoesNotExist:
        return JsonResponse({'error': 'Reabastecimiento no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@check_user_role(allowed_roles=['Administrador'])
def get_edit_form_api(request, pk):
    """
    API endpoint to fetch the edit form for a Reabastecimiento and render partial HTML.
    """
    try:
        reabastecimiento = get_object_or_404(Reabastecimiento, pk=pk)
        
        # Check conditions preventing edit
        if Lote.objects.filter(reabastecimiento_detalle__reabastecimiento=reabastecimiento, ventadetalle__isnull=False).exists():
            return JsonResponse({'error': 'No se puede editar, tiene productos vendidos.'}, status=400)
        if reabastecimiento.estado == Reabastecimiento.ESTADO_RECIBIDO:
            return JsonResponse({'error': 'No se puede editar un reabastecimiento recibido.'}, status=400)

        # Instantiate the form and formset
        form = ReabastecimientoForm(instance=reabastecimiento)
        formset = ReabastecimientoDetalleFormSet(instance=reabastecimiento, queryset=ReabastecimientoDetalle.objects.filter(reabastecimiento=reabastecimiento))
        
        # Products for the formset selects
        all_products_data = list(Producto.objects.values('id', 'nombre', 'precio_unitario'))

        context = {
            'form': form,
            'formset': formset,
            'reabastecimiento_id': pk,
            'all_products_json': json.dumps(all_products_data, cls=DjangoJSONEncoder),
        }
        html_content = render_to_string('suppliers/partials/reabastecimiento_edit_form.html', context, request=request)
        return JsonResponse({'html': html_content})
    except Reabastecimiento.DoesNotExist:
        return JsonResponse({'error': 'Reabastecimiento no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@check_user_role(allowed_roles=['Administrador'])
def api_search_proveedores(request):
    """
    API endpoint to search for suppliers by name for Select2.
    Retorna resultados en formato compatible con Select2.
    """
    term = request.GET.get('term', '')
    if term and len(term) >= 2:
        proveedores = Proveedor.objects.filter(
            Q(nombre_empresa__icontains=term) | 
            Q(documento_identificacion__icontains=term)
        ).values('id', 'nombre_empresa')[:10]
        results = [{'id': p['id'], 'text': p['nombre_empresa']} for p in proveedores]
    else:
        results = []
    return JsonResponse({'results': results})

@login_required
@check_user_role(allowed_roles=['Administrador'])
def api_search_productos(request):
    """
    API endpoint to search for products by name for Select2.
    Retorna resultados en formato compatible con Select2.
    """
    term = request.GET.get('term', '')
    if term and len(term) >= 2:
        productos = Producto.objects.filter(nombre__icontains=term).values('id', 'nombre')[:10]
        results = [{'id': p['id'], 'text': p['nombre']} for p in productos]
    else:
        results = []
    return JsonResponse({'results': results})




@login_required
@check_user_role(allowed_roles=['Administrador'])
def reabastecimiento_row_api(request, pk):
    """
    API endpoint para obtener una fila de reabastecimiento actualizada.
    """
    try:
        reabastecimiento = get_object_or_404(Reabastecimiento, pk=pk)
        html = render_to_string('suppliers/partials/reabastecimiento_row.html', {
            'r': reabastecimiento
        }, request=request)
        return JsonResponse({'html': html})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@check_user_role(allowed_roles=['Administrador'])
def reabastecimiento_detail_api(request, pk):
    """
    API endpoint para obtener detalles de un reabastecimiento en JSON.
    """
    try:
        reab = get_object_or_404(Reabastecimiento, pk=pk)
        detalles = reab.reabastecimientodetalle_set.all()
        
        data = {
            'id': reab.pk,
            'proveedor_nombre': reab.proveedor.nombre_empresa,
            'estado': reab.estado,
            'costo_total': str(reab.costo_total),
            'iva': str(reab.iva),
            'detalles': [
                {
                    'id': d.pk,
                    'producto_nombre': d.producto.nombre,
                    'cantidad': d.cantidad,
                    'cantidad_recibida': d.cantidad_recibida,
                    'costo_unitario': str(d.costo_unitario),
                    'fecha_caducidad': d.fecha_caducidad.isoformat() if d.fecha_caducidad else None,
                    'numero_lote': d.numero_lote or '',
                }
                for d in detalles
            ]
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@never_cache
@login_required
@check_user_role(allowed_roles=['Administrador'])
@require_POST
def reabastecimiento_recibir(request, pk):
    """
    Marcar un reabastecimiento como 'recibido' y crear lotes.
    Envía correo de discrepancia si hay diferencias en cantidades.
    """
    try:
        data = json.loads(request.body)
        with transaction.atomic():
            reab = get_object_or_404(Reabastecimiento, pk=pk)
            
            if reab.estado == Reabastecimiento.ESTADO_RECIBIDO:
                return JsonResponse({'error': 'Este reabastecimiento ya ha sido recibido.'}, status=400)

            discrepancias_productos = []
            detalles_recibidos = []

            for detalle_data in data.get('detalles', []):
                detalle = get_object_or_404(ReabastecimientoDetalle, pk=detalle_data.get('id'), reabastecimiento=reab)
                cantidad_recibida = int(detalle_data.get('cantidad_recibida', 0))
                fecha_caducidad_str = detalle_data.get('fecha_caducidad')
                numero_lote = detalle_data.get('numero_lote', '')

                if cantidad_recibida > detalle.cantidad:
                    raise ValueError(f'Cantidad recibida ({cantidad_recibida}) > solicitada ({detalle.cantidad}) para {detalle.producto.nombre}.')
                
                # Registrar discrepancias
                if cantidad_recibida < detalle.cantidad and cantidad_recibida > 0:
                    discrepancias_productos.append({
                        'producto_nombre': detalle.producto.nombre,
                        'cantidad_solicitada': detalle.cantidad,
                        'cantidad_recibida': cantidad_recibida,
                    })

                # Actualizar detalle
                detalle.cantidad_recibida = cantidad_recibida
                if fecha_caducidad_str:
                    detalle.fecha_caducidad = fecha_caducidad_str
                if numero_lote:
                    detalle.numero_lote = numero_lote
                detalle.recibido_por = request.user
                detalle.fecha_recepcion = timezone.now()
                detalle.save()

                if cantidad_recibida > 0:
                    if not fecha_caducidad_str:
                        raise ValueError(f'Debe proporcionar una fecha de caducidad para {detalle.producto.nombre}.')

                    # Generar número de lote si no se proporciona
                    if not numero_lote:
                        numero_lote = f"R{reab.pk}-P{detalle.producto.pk}-{detalle.pk}"
                    
                    lote = Lote.objects.create(
                        producto=detalle.producto, 
                        reabastecimiento_detalle=detalle, 
                        numero_lote=numero_lote,
                        cantidad_disponible=cantidad_recibida,
                        costo_unitario_lote=detalle.costo_unitario,
                        fecha_caducidad=fecha_caducidad_str
                    )
                    MovimientoInventario.objects.create(
                        producto=lote.producto, 
                        lote=lote, 
                        cantidad=cantidad_recibida, 
                        tipo_movimiento='entrada',
                        descripcion=f'Entrada por reabastecimiento #{reab.pk}', 
                        reabastecimiento_id=reab.pk
                    )
                    
                    detalles_recibidos.append({
                        'producto': detalle.producto.nombre,
                        'cantidad': cantidad_recibida,
                        'lote': numero_lote
                    })

            # Cambiar estado
            reab.estado = Reabastecimiento.ESTADO_RECIBIDO
            reab.save()

            # Enviar email de discrepancias si las hay
            if discrepancias_productos:
                send_discrepancy_email(reab, discrepancias_productos)

            return JsonResponse({
                'message': 'Reabastecimiento recibido y stock actualizado.',
                'estado': reab.get_estado_display(),
                'detalles_recibidos': len(detalles_recibidos),
                'discrepancias': len(discrepancias_productos)
            })
    except Exception as e:
        print(f"ERROR en reabastecimiento_recibir: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@never_cache
@login_required
@check_user_role(allowed_roles=['Administrador'])
@require_POST
def reabastecimiento_update_received(request, pk):
    """
    Permitir edición limitada post-recepción (solo fecha y lote).
    """
    try:
        data = json.loads(request.body)
        with transaction.atomic():
            reab = get_object_or_404(Reabastecimiento, pk=pk)
            
            if reab.estado != Reabastecimiento.ESTADO_RECIBIDO:
                return JsonResponse({'error': 'Solo se puede editar recepciones completadas'}, status=400)

            cambios_realizados = []

            for detalle_data in data.get('detalles', []):
                detalle = get_object_or_404(ReabastecimientoDetalle, pk=detalle_data.get('id'), reabastecimiento=reab)
                
                # Solo permitir cambios en fecha_caducidad y numero_lote
                nueva_fecha = detalle_data.get('fecha_caducidad')
                nuevo_lote = detalle_data.get('numero_lote')
                
                cambio = False
                
                if nueva_fecha and detalle.fecha_caducidad != nueva_fecha:
                    detalle.fecha_caducidad = nueva_fecha
                    cambio = True
                    cambios_realizados.append(f"{detalle.producto.nombre}: fecha actualizada")
                
                if nuevo_lote and detalle.numero_lote != nuevo_lote:
                    detalle.numero_lote = nuevo_lote
                    cambio = True
                    cambios_realizados.append(f"{detalle.producto.nombre}: lote actualizado")
                
                if cambio:
                    detalle.save()

            return JsonResponse({
                'message': 'Cambios guardados correctamente',
                'cambios': len(cambios_realizados)
            })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
