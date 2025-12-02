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
from .models import Pqrs, PqrsEvento, PqrsAdjunto
from .forms import PqrsForm, PqrsUpdateForm
from .utils import enviar_correo_respuesta, enviar_correo_cambio_estado
from clients.models import Cliente
from users.decorators import check_user_role


@login_required
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def pqrs_list(request):
    base_query = Pqrs.objects.select_related('cliente', 'creado_por').order_by('-fecha_creacion')
    query = request.GET.get('q')
    tipo = request.GET.get('tipo')
    estado = request.GET.get('estado')

    pqrs_query = base_query.all()

    if query:
        pqrs_query = pqrs_query.filter(            
            models.Q(cliente__nombres__icontains=query) |
            models.Q(cliente__apellidos__icontains=query) |
            models.Q(tipo__icontains=query) |
            models.Q(estado__icontains=query)
        )
    if tipo:
        pqrs_query = pqrs_query.filter(tipo=tipo)
    if estado:
        pqrs_query = pqrs_query.filter(estado=estado)


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

    context = {
        'pqrs': page_obj,
        'stats': stats,
        'query': query,
        'tipos': Pqrs.TIPO_CHOICES,
        'estados': Pqrs.ESTADO_CHOICES,
        'selected_tipo': tipo,
        'selected_estado': estado,
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
                pqrs.save()
                
                # Crear evento de creación
                PqrsEvento.objects.create(
                    pqrs=pqrs,
                    usuario=request.user,
                    tipo_evento=PqrsEvento.EVENTO_CREACION,
                    comentario=f'PQRS creado: {pqrs.get_tipo_display()}'
                )
                
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
    eventos = PqrsEvento.objects.filter(pqrs=pqrs)
    adjuntos = PqrsAdjunto.objects.filter(pqrs=pqrs)
    form = PqrsUpdateForm(instance=pqrs)
    context = {
        'pqrs': pqrs,
        'eventos': eventos,
        'adjuntos': adjuntos,
        'form': form,
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

            # 1. Handle Response Saving
            if action == 'save_response':
                respuesta = form.cleaned_data.get('respuesta')
                if not respuesta:
                    messages.error(request, 'Debe escribir una respuesta.')
                    return redirect('pqrs:pqrs_detail', pk=pk)
                
                # Guardar respuesta en el PQRS
                pqrs.ultima_respuesta_enviada = respuesta
                pqrs.save()
                
                # Crear evento
                evento = PqrsEvento.objects.create(
                    pqrs=pqrs,
                    usuario=request.user,
                    tipo_evento=PqrsEvento.EVENTO_RESPUESTA,
                    comentario=respuesta,
                    es_visible_cliente=True
                )
                
                # Enviar correo al cliente
                if enviar_correo_respuesta(pqrs, respuesta):
                    pqrs.correo_enviado = True
                    pqrs.fecha_ultimo_correo = timezone.now()
                    pqrs.save()
                    
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
                if not observacion_estado:
                    messages.error(request, 'Debe proporcionar una observación para el cambio de estado.')
                    return redirect('pqrs:pqrs_detail', pk=pk)
                
                pqrs.estado = estado_nuevo
                if estado_nuevo == Pqrs.ESTADO_CERRADO:
                    pqrs.fecha_cierre = timezone.now()
                pqrs.save()

                PqrsEvento.objects.create(
                    pqrs=pqrs,
                    usuario=request.user,
                    tipo_evento=PqrsEvento.EVENTO_ESTADO,
                    comentario=f'Cambio de estado: {estado_anterior} → {estado_nuevo}. Observación: {observacion_estado}',
                    es_visible_cliente=False
                )
                
                # Enviar correo de notificación al cliente
                enviar_correo_cambio_estado(pqrs, estado_anterior, estado_nuevo, observacion_estado)
                
                messages.success(request, f'PQRS actualizado al estado: {pqrs.get_estado_display()}.')
            
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
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")

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
    
    return JsonResponse({
        'message': 'Archivo subido exitosamente.',
        'adjunto': {
            'id': adjunto.id,
            'nombre': adjunto.nombre_archivo,
            'tamano': adjunto.tamano_bytes,
            'fecha': adjunto.fecha_subida.strftime('%d/%m/%Y %H:%M')
        }
    })


@never_cache
@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador'])
def pqrs_delete(request, pk):
    pqrs = get_object_or_404(Pqrs, pk=pk)
    pqrs.delete()
    return JsonResponse({'message': 'PQRS eliminado exitosamente.'})