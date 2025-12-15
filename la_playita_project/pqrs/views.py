from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.db import models
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import logging
from .models import (
    Pqrs, PqrsEvento, PqrsAdjunto, PqrsCalificacion, PqrsEscalamiento,
    PqrsSla, PqrsPlantillaRespuesta, PqrsVistaGuardada, PqrsNotificacion
)
from .forms import PqrsForm, PqrsUpdateForm, PqrsAsignarForm, PqrsCalificacionForm
from .utils import enviar_correo_respuesta, enviar_correo_cambio_estado
from clients.models import Cliente
from users.decorators import check_user_role
from datetime import timedelta

logger = logging.getLogger(__name__)


@login_required
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def pqrs_dashboard(request):
    """Dashboard principal con métricas en tiempo real"""
    
    # Casos del usuario actual
    mis_casos = Pqrs.objects.filter(
        asignado_a=request.user
    ).exclude(estado='cerrado').select_related('cliente', 'asignado_a')
    
    # Casos urgentes activos
    casos_urgentes = Pqrs.objects.filter(
        prioridad='urgente',
        estado__in=['nuevo', 'en_proceso']
    ).select_related('cliente', 'asignado_a').order_by('fecha_creacion')[:5]
    
    # Casos con SLA próximo a vencer (menos de 2 horas)
    casos_sla_critico = []
    for caso in Pqrs.objects.filter(estado__in=['nuevo', 'en_proceso'], fecha_limite_sla__isnull=False):
        if caso.fecha_limite_sla:
            tiempo_restante = (caso.fecha_limite_sla - timezone.now()).total_seconds() / 3600
            if 0 < tiempo_restante <= 2:
                casos_sla_critico.append({
                    'caso': caso,
                    'horas_restantes': round(tiempo_restante, 1)
                })
    
    # Estadísticas de tendencia (últimos 30 días)
    hace_30_dias = timezone.now() - timedelta(days=30)
    from django.db.models.functions import TruncDate
    tendencia = list(Pqrs.objects.filter(
        fecha_creacion__gte=hace_30_dias
    ).annotate(
        dia=TruncDate('fecha_creacion')
    ).values('dia').annotate(
        total=models.Count('id')
    ).order_by('dia'))
    
    # Convertir fechas a string para JSON
    import json
    tendencia_json = json.dumps([{
        'dia': item['dia'].strftime('%d/%m') if item['dia'] else '',
        'total': item['total']
    } for item in tendencia if item['dia']])
    
    # Métricas comparativas
    hace_7_dias = timezone.now() - timedelta(days=7)
    hace_14_dias = timezone.now() - timedelta(days=14)
    
    casos_semana_actual = Pqrs.objects.filter(fecha_creacion__gte=hace_7_dias).count()
    casos_semana_anterior = Pqrs.objects.filter(
        fecha_creacion__gte=hace_14_dias,
        fecha_creacion__lt=hace_7_dias
    ).count()
    
    variacion_semanal = 0
    if casos_semana_anterior > 0:
        variacion_semanal = ((casos_semana_actual - casos_semana_anterior) / casos_semana_anterior) * 100
    
    context = {
        'mis_casos': mis_casos,
        'casos_urgentes': casos_urgentes,
        'casos_sla_critico': casos_sla_critico,
        'tendencia': tendencia_json,
        'variacion_semanal': round(variacion_semanal, 1),
        'stats': {
            'total': Pqrs.objects.count(),
            'casos_nuevos': Pqrs.objects.filter(estado='nuevo').count(),
            'casos_en_proceso': Pqrs.objects.filter(estado='en_proceso').count(),
            'casos_resueltos': Pqrs.objects.filter(estado='resuelto').count(),
            'casos_cerrados': Pqrs.objects.filter(estado='cerrado').count(),
        }
    }
    
    return render(request, 'pqrs/dashboard.html', context)


@login_required
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def pqrs_list(request):
    base_query = Pqrs.objects.select_related('cliente', 'creado_por', 'asignado_a').order_by('-fecha_creacion')
    query = request.GET.get('q')
    tipo = request.GET.get('tipo')
    estado = request.GET.get('estado')
    mis_casos = request.GET.get('mis_casos')

    pqrs_query = base_query.all()

    if query:
        pqrs_query = pqrs_query.filter(            
            models.Q(cliente__nombres__icontains=query) |
            models.Q(cliente__apellidos__icontains=query) |
            models.Q(numero_caso__icontains=query) |
            models.Q(tipo__icontains=query) |
            models.Q(estado__icontains=query)
        )
    if tipo:
        pqrs_query = pqrs_query.filter(tipo=tipo)
    if estado:
        pqrs_query = pqrs_query.filter(estado=estado)
    if mis_casos:
        pqrs_query = pqrs_query.filter(asignado_a=request.user)


    # Calculate statistics
    stats_query = pqrs_query if (query or tipo or estado) else base_query
    stats = stats_query.aggregate(
        total=models.Count('id'),
        nuevos=models.Count('id', filter=models.Q(estado='nuevo')),
        en_proceso=models.Count('id', filter=models.Q(estado='en_proceso')),
        resueltos=models.Count('id', filter=models.Q(estado='resuelto')),
        cerrados=models.Count('id', filter=models.Q(estado='cerrado')),
    )

    paginator = Paginator(pqrs_query, 10) # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calcular SLA para cada caso en la página actual
    for caso in page_obj:
        if caso.fecha_limite_sla:
            tiempo_restante = (caso.fecha_limite_sla - timezone.now()).total_seconds() / 3600
            caso.sla_horas_restantes = round(tiempo_restante, 1)
            if tiempo_restante < 0:
                caso.sla_estado = 'vencido'
            elif tiempo_restante < 2:
                caso.sla_estado = 'critico'
            elif tiempo_restante < 6:
                caso.sla_estado = 'warning'
            else:
                caso.sla_estado = 'ok'
        else:
            caso.sla_horas_restantes = None
            caso.sla_estado = 'sin_sla'

    context = {
        'pqrs': page_obj,
        'stats': stats,
        'query': query,
        'tipos': Pqrs.TIPO_CHOICES,
        'estados': Pqrs.ESTADO_CHOICES,
        'selected_tipo': tipo,
        'selected_estado': estado,
        'mis_casos': mis_casos,
    }
    return render(request, 'pqrs/pqrs_list.html', context)


@login_required
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def pqrs_create(request):
    if request.method == 'POST':
        form = PqrsForm(request.POST)
        if form.is_valid():
            pqrs = form.save(commit=False)
            cliente_id = request.POST.get('cliente')
            try:
                cliente = Cliente.objects.get(id=cliente_id)
                pqrs.cliente = cliente
                pqrs.creado_por = request.user
                # Auto-asignar al creador por defecto
                pqrs.asignado_a = request.user
                pqrs.save()
                # El evento de creación se genera automáticamente por el signal
                
                messages.success(request, f'PQRS {pqrs.numero_caso} creado exitosamente.')
                return redirect(reverse('pqrs:pqrs_detail', kwargs={'pk': pqrs.id}))
            except Cliente.DoesNotExist:
                messages.error(request, f'No se encontró un cliente con el ID {cliente_id}.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = PqrsForm()

    clientes = Cliente.objects.all()
    context = {
        'form': form,
        'clientes': clientes,
    }
    return render(request, 'pqrs/pqrs_create.html', context)


@login_required
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def pqrs_detail(request, pk):
    pqrs = get_object_or_404(Pqrs, pk=pk)
    eventos = PqrsEvento.objects.filter(pqrs=pqrs).order_by('-fecha_evento')
    adjuntos = PqrsAdjunto.objects.filter(pqrs=pqrs)
    form = PqrsUpdateForm(instance=pqrs)
    asignar_form = PqrsAsignarForm(instance=pqrs)
    
    # Calcular SLA
    if pqrs.fecha_limite_sla:
        tiempo_restante = (pqrs.fecha_limite_sla - timezone.now()).total_seconds() / 3600
        pqrs.sla_horas_restantes = round(tiempo_restante, 1)
        if tiempo_restante < 0:
            pqrs.sla_estado = 'vencido'
            pqrs.sla_vencido = True
        elif tiempo_restante < 2:
            pqrs.sla_estado = 'critico'
        elif tiempo_restante < 6:
            pqrs.sla_estado = 'warning'
        else:
            pqrs.sla_estado = 'ok'
    
    # Verificar si ya tiene calificación
    try:
        calificacion = pqrs.calificacion
    except PqrsCalificacion.DoesNotExist:
        calificacion = None
    
    context = {
        'pqrs': pqrs,
        'eventos': eventos,
        'adjuntos': adjuntos,
        'form': form,
        'asignar_form': asignar_form,
        'calificacion': calificacion,
    }
    return render(request, 'pqrs/pqrs_detail.html', context)

@login_required
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def pqrs_update(request, pk):
    pqrs = get_object_or_404(Pqrs, pk=pk)
    if request.method == 'POST':
        form = PqrsUpdateForm(request.POST)
        
        if form.is_valid():
            action = request.POST.get('action')
            logger.info(f"Acción recibida: {action}, Estado actual: {pqrs.estado}")

            # 1. Handle Response Saving
            if action == 'save_response':
                respuesta = form.cleaned_data.get('respuesta')
                if not respuesta:
                    messages.error(request, 'Debe escribir una respuesta.')
                    return redirect('pqrs:pqrs_detail', pk=pk)
                
                # Crear evento de respuesta
                evento = PqrsEvento.objects.create(
                    pqrs=pqrs,
                    usuario=request.user,
                    tipo_evento=PqrsEvento.EVENTO_RESPUESTA,
                    comentario=respuesta,
                    es_visible_cliente=True
                )
                
                # Actualizar fecha de primera respuesta si es la primera vez
                if not pqrs.fecha_primera_respuesta:
                    pqrs.fecha_primera_respuesta = timezone.now()
                    pqrs.save()
                
                # Enviar correo al cliente
                if enviar_correo_respuesta(pqrs, respuesta):
                    evento.enviado_por_correo = True
                    evento.fecha_envio_correo = timezone.now()
                    evento.save()
                    
                    messages.success(request, 'Respuesta guardada y correo enviado exitosamente.')
                else:
                    messages.warning(request, 'Respuesta guardada, pero hubo un error al enviar el correo.')

            # 2. Handle State Changes
            estado_anterior = pqrs.estado
            estado_nuevo = estado_anterior
            observacion_estado = form.cleaned_data.get('observacion_estado')

            is_state_change_action = False
            if action == 'start_processing':
                estado_nuevo = Pqrs.ESTADO_EN_PROCESO
                is_state_change_action = True
            elif action == 'resolve':
                estado_nuevo = Pqrs.ESTADO_RESUELTO
                is_state_change_action = True
            elif action == 'close':
                estado_nuevo = Pqrs.ESTADO_CERRADO
                is_state_change_action = True
            
            if is_state_change_action:
                logger.info(f"is_state_change_action=True, observacion_estado={observacion_estado}")
                
                if not observacion_estado:
                    messages.error(request, 'Debe proporcionar una observación para el cambio de estado.')
                    return redirect('pqrs:pqrs_detail', pk=pk)
                
                logger.info(f"Comparando estados: {estado_anterior} != {estado_nuevo}")
                
                # Solo procesar si el estado realmente cambia
                if estado_anterior != estado_nuevo:
                    logger.info(f"Cambiando estado de {estado_anterior} a {estado_nuevo}")
                    
                    # Obtener nombres legibles de los estados
                    estado_anterior_display = dict(Pqrs.ESTADO_CHOICES).get(estado_anterior, estado_anterior)
                    estado_nuevo_display = dict(Pqrs.ESTADO_CHOICES).get(estado_nuevo, estado_nuevo)
                    
                    pqrs.estado = estado_nuevo
                    if estado_nuevo == Pqrs.ESTADO_CERRADO:
                        pqrs.fecha_cierre = timezone.now()
                    pqrs.save()
                    logger.info(f"Estado guardado: {pqrs.estado}")

                    PqrsEvento.objects.create(
                        pqrs=pqrs,
                        usuario=request.user,
                        tipo_evento=PqrsEvento.EVENTO_ESTADO,
                        comentario=f'Cambio de estado: {estado_anterior_display} → {estado_nuevo_display}. Observación: {observacion_estado}',
                        es_visible_cliente=False
                    )
                    
                    # Enviar correo de notificación al cliente
                    enviar_correo_cambio_estado(pqrs, estado_anterior, estado_nuevo, observacion_estado)
                    
                    messages.success(request, f'PQRS actualizado al estado: {pqrs.get_estado_display()}.')
                else:
                    logger.warning(f"Estado no cambió: {estado_anterior} == {estado_nuevo}")
                    messages.info(request, 'El PQRS ya se encuentra en ese estado.')
            
            # 3. Handle Internal Note
            nota_interna = form.cleaned_data.get('nota_interna')
            if action == 'save_internal_note':
                if not nota_interna:
                    messages.error(request, 'Debe proporcionar contenido para la nota interna.')
                    return redirect('pqrs:pqrs_detail', pk=pk)
                
                PqrsEvento.objects.create(
                    pqrs=pqrs,
                    usuario=request.user,
                    tipo_evento=PqrsEvento.EVENTO_NOTA,
                    comentario=nota_interna,
                    es_visible_cliente=False
                )
                messages.success(request, 'Nota interna guardada exitosamente.')

        else:
            # Debug: Log de errores de validación
            logger.error(f"Errores de validación del formulario: {form.errors}")
            
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields.get(field, field)}: {error}")

    return redirect(reverse('pqrs:pqrs_detail', kwargs={'pk': pk}))


@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def pqrs_upload_adjunto(request, pk):
    pqrs = get_object_or_404(Pqrs, pk=pk)
    
    if 'archivo' not in request.FILES:
        return JsonResponse({'error': 'No se proporcionó ningún archivo.'}, status=400)
    
    archivo = request.FILES['archivo']
    descripcion = request.POST.get('descripcion', '')
    
    # Validar tamaño (máximo 10MB)
    if archivo.size > 10 * 1024 * 1024:
        return JsonResponse({'error': 'El archivo es demasiado grande. Máximo 10MB.'}, status=400)
    
    # Validar tipo de archivo
    tipos_permitidos = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'application/msword', 
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
    
    if archivo.content_type not in tipos_permitidos:
        return JsonResponse({'error': 'Tipo de archivo no permitido.'}, status=400)
    
    # Crear directorio si no existe
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'pqrs_adjuntos', str(pqrs.id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Guardar archivo
    fs = FileSystemStorage(location=upload_dir)
    filename = fs.save(archivo.name, archivo)
    file_path = os.path.join('pqrs_adjuntos', str(pqrs.id), filename)
    
    # Crear registro en base de datos
    adjunto = PqrsAdjunto.objects.create(
        pqrs=pqrs,
        nombre_archivo=archivo.name,
        ruta_archivo=file_path,
        tipo_mime=archivo.content_type,
        tamano_bytes=archivo.size,
        descripcion=descripcion,
        subido_por=request.user
    )
    
    # Crear evento en el timeline
    tipo_archivo = "imagen" if "image" in archivo.content_type else "documento"
    comentario = f'Archivo adjunto: {archivo.name} ({tipo_archivo})'
    if descripcion:
        comentario += f' - {descripcion}'
    
    PqrsEvento.objects.create(
        pqrs=pqrs,
        usuario=request.user,
        tipo_evento=PqrsEvento.EVENTO_NOTA,
        comentario=comentario,
        es_visible_cliente=False
    )
    
    return JsonResponse({
        'message': 'Archivo subido exitosamente.',
        'adjunto': {
            'id': adjunto.id,
            'nombre': adjunto.nombre_archivo,
            'tamano': adjunto.tamano_bytes,
            'fecha': adjunto.fecha_subida.strftime('%d/%m/%Y %H:%M')
        }
    })


@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def pqrs_asignar(request, pk):
    pqrs = get_object_or_404(Pqrs, pk=pk)
    form = PqrsAsignarForm(request.POST, instance=pqrs)
    
    if form.is_valid():
        asignado_anterior = pqrs.asignado_a
        pqrs = form.save()
        
        # Crear evento de asignación
        PqrsEvento.objects.create(
            pqrs=pqrs,
            usuario=request.user,
            tipo_evento=PqrsEvento.EVENTO_NOTA,
            comentario=f'Caso reasignado de {asignado_anterior} a {pqrs.asignado_a}',
            es_visible_cliente=False
        )
        
        # Notificación simple (puedes mejorar con email o notificaciones push)
        if pqrs.asignado_a != request.user:
            messages.info(request, f'Se ha notificado a {pqrs.asignado_a.get_full_name() or pqrs.asignado_a.username} sobre la asignación.')
        
        messages.success(request, f'Caso asignado a {pqrs.asignado_a.get_full_name() or pqrs.asignado_a.username}')
    else:
        messages.error(request, 'Error al asignar el caso.')
    
    return redirect(reverse('pqrs:pqrs_detail', kwargs={'pk': pk}))


@never_cache
@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador'])
def pqrs_delete(request, pk):
    pqrs = get_object_or_404(Pqrs, pk=pk)
    pqrs.delete()
    return JsonResponse({'message': 'PQRS eliminado exitosamente.'})



@login_required
@check_user_role(allowed_roles=['Administrador'])
def pqrs_estadisticas(request):
    """Vista de estadísticas generales del módulo PQRS"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Estadísticas generales
        cursor.execute("""
            SELECT 
                COUNT(*) as total_casos,
                SUM(CASE WHEN estado = 'nuevo' THEN 1 ELSE 0 END) as casos_nuevos,
                SUM(CASE WHEN estado = 'en_proceso' THEN 1 ELSE 0 END) as casos_en_proceso,
                SUM(CASE WHEN estado = 'resuelto' THEN 1 ELSE 0 END) as casos_resueltos,
                SUM(CASE WHEN estado = 'cerrado' THEN 1 ELSE 0 END) as casos_cerrados,
                SUM(CASE WHEN prioridad = 'urgente' THEN 1 ELSE 0 END) as casos_urgentes,
                SUM(CASE WHEN prioridad = 'alta' THEN 1 ELSE 0 END) as casos_alta_prioridad,
                AVG(tiempo_resolucion_horas) as tiempo_promedio_resolucion_horas,
                COUNT(DISTINCT cliente_id) as clientes_unicos,
                SUM(CASE WHEN fecha_creacion >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) as casos_ultima_semana,
                SUM(CASE WHEN fecha_creacion >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 ELSE 0 END) as casos_ultimo_mes
            FROM pqrs
        """)
        stats_generales = cursor.fetchone()
        
        # Estadísticas por usuario
        cursor.execute("""
            SELECT 
                u.id,
                u.nombres,
                u.apellidos,
                COUNT(p.id) as total_casos_asignados,
                SUM(CASE WHEN p.estado = 'nuevo' THEN 1 ELSE 0 END) as casos_nuevos,
                SUM(CASE WHEN p.estado = 'en_proceso' THEN 1 ELSE 0 END) as casos_en_proceso,
                SUM(CASE WHEN p.estado = 'resuelto' THEN 1 ELSE 0 END) as casos_resueltos,
                SUM(CASE WHEN p.estado = 'cerrado' THEN 1 ELSE 0 END) as casos_cerrados,
                AVG(p.tiempo_resolucion_horas) as tiempo_promedio_resolucion
            FROM usuario u
            LEFT JOIN pqrs p ON u.id = p.asignado_a_id
            GROUP BY u.id, u.nombres, u.apellidos
            HAVING total_casos_asignados > 0
            ORDER BY total_casos_asignados DESC
        """)
        stats_por_usuario = cursor.fetchall()
        
        # Estadísticas por tipo
        cursor.execute("""
            SELECT 
                tipo,
                COUNT(*) as total,
                AVG(tiempo_resolucion_horas) as tiempo_promedio
            FROM pqrs
            GROUP BY tipo
            ORDER BY total DESC
        """)
        stats_por_tipo = cursor.fetchall()
        
        # Estadísticas por canal
        cursor.execute("""
            SELECT 
                canal_origen,
                COUNT(*) as total
            FROM pqrs
            GROUP BY canal_origen
            ORDER BY total DESC
        """)
        stats_por_canal = cursor.fetchall()
    
    context = {
        'stats_generales': {
            'total_casos': stats_generales[0] or 0,
            'casos_nuevos': stats_generales[1] or 0,
            'casos_en_proceso': stats_generales[2] or 0,
            'casos_resueltos': stats_generales[3] or 0,
            'casos_cerrados': stats_generales[4] or 0,
            'casos_urgentes': stats_generales[5] or 0,
            'casos_alta_prioridad': stats_generales[6] or 0,
            'tiempo_promedio_resolucion': round(stats_generales[7] or 0, 2),
            'clientes_unicos': stats_generales[8] or 0,
            'casos_ultima_semana': stats_generales[9] or 0,
            'casos_ultimo_mes': stats_generales[10] or 0,
        },
        'stats_por_usuario': stats_por_usuario,
        'stats_por_tipo': stats_por_tipo,
        'stats_por_canal': stats_por_canal,
    }
    
    return render(request, 'pqrs/pqrs_estadisticas.html', context)


@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def pqrs_calificar(request, pk):
    """Vista para que el cliente califique el PQRS"""
    pqrs = get_object_or_404(Pqrs, pk=pk)
    
    # Verificar que el caso esté cerrado
    if pqrs.estado != Pqrs.ESTADO_CERRADO:
        messages.error(request, 'Solo se pueden calificar casos cerrados.')
        return redirect(reverse('pqrs:pqrs_detail', kwargs={'pk': pk}))
    
    # Verificar que no tenga calificación previa
    if hasattr(pqrs, 'calificacion'):
        messages.warning(request, 'Este caso ya ha sido calificado.')
        return redirect(reverse('pqrs:pqrs_detail', kwargs={'pk': pk}))
    
    form = PqrsCalificacionForm(request.POST)
    if form.is_valid():
        calificacion = form.save(commit=False)
        calificacion.pqrs = pqrs
        calificacion.save()
        
        # Crear evento
        PqrsEvento.objects.create(
            pqrs=pqrs,
            usuario=None,
            tipo_evento=PqrsEvento.EVENTO_NOTA,
            comentario=f'Cliente calificó con {calificacion.puntuacion} estrellas',
            es_visible_cliente=True
        )
        
        messages.success(request, '¡Gracias por tu calificación!')
    else:
        messages.error(request, 'Error al guardar la calificación.')
    
    return redirect(reverse('pqrs:pqrs_detail', kwargs={'pk': pk}))


@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def pqrs_escalar(request, pk):
    """Vista para escalar un PQRS"""
    pqrs = get_object_or_404(Pqrs, pk=pk)
    
    escalado_a_id = request.POST.get('escalado_a')
    motivo = request.POST.get('motivo')
    
    if not escalado_a_id or not motivo:
        messages.error(request, 'Debe seleccionar un usuario y proporcionar un motivo.')
        return redirect(reverse('pqrs:pqrs_detail', kwargs={'pk': pk}))
    
    from users.models import Usuario
    try:
        escalado_a = Usuario.objects.get(id=escalado_a_id)
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect(reverse('pqrs:pqrs_detail', kwargs={'pk': pk}))
    
    # Crear escalamiento
    from .models import PqrsEscalamiento
    escalamiento = PqrsEscalamiento.objects.create(
        pqrs=pqrs,
        escalado_por=request.user,
        escalado_a=escalado_a,
        motivo=motivo
    )
    
    # Reasignar el caso
    pqrs.asignado_a = escalado_a
    pqrs.save()
    
    # Crear evento
    PqrsEvento.objects.create(
        pqrs=pqrs,
        usuario=request.user,
        tipo_evento=PqrsEvento.EVENTO_NOTA,
        comentario=f'Caso escalado a {escalado_a.get_full_name() or escalado_a.username}. Motivo: {motivo}',
        es_visible_cliente=False
    )
    
    messages.success(request, f'Caso escalado exitosamente a {escalado_a.get_full_name() or escalado_a.username}')
    return redirect(reverse('pqrs:pqrs_detail', kwargs={'pk': pk}))
