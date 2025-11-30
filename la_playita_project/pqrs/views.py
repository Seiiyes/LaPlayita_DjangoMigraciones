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
from .models import Pqrs, PqrsEvento
from .forms import PqrsForm, PqrsUpdateForm
from clients.models import Cliente
from users.decorators import check_user_role


@login_required
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def pqrs_list(request):
    base_query = Pqrs.objects.select_related('cliente', 'usuario').order_by('-fecha_creacion')
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
                pqrs.usuario = request.user
                pqrs.save()
                messages.success(request, 'PQRS creado exitosamente.')
                return redirect(reverse('pqrs:pqrs_list'))
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
    form = PqrsUpdateForm(instance=pqrs)
    context = {
        'pqrs': pqrs,
        'eventos': eventos,
        'form': form,
    }
    return render(request, 'pqrs/pqrs_detail.html', context)

@login_required
@check_user_role(allowed_roles=['Administrador', 'Vendedor'])
def pqrs_update(request, pk):
    pqrs = get_object_or_404(Pqrs, pk=pk)
    if request.method == 'POST':
        form = PqrsUpdateForm(request.POST, instance=pqrs)
        if form.is_valid():
            action = request.POST.get('action')
            
            # Save the form data (respuesta and descripcion_cambio)
            pqrs_actualizado = form.save(commit=False)

            # 1. Handle Response Saving
            if action == 'save_response' and form.cleaned_data.get('respuesta'):
                pqrs_actualizado.save()
                PqrsEvento.objects.create(
                    pqrs=pqrs_actualizado,
                    usuario=request.user,
                    tipo_evento=PqrsEvento.EVENTO_RESPUESTA,
                    comentario=form.cleaned_data.get('respuesta')
                )
                messages.success(request, 'Respuesta guardada exitosamente.')

            # 2. Handle State Changes
            estado_anterior = pqrs.estado
            estado_nuevo = estado_anterior
            
            # Get observation for state change
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
                
                pqrs_actualizado.estado = estado_nuevo
                pqrs_actualizado.save()

                PqrsEvento.objects.create(
                    pqrs=pqrs_actualizado,
                    usuario=request.user,
                    tipo_evento=PqrsEvento.EVENTO_ESTADO,
                    comentario=f'Cambio de estado: {estado_anterior} → {estado_nuevo}. Observación: {observacion_estado}'
                )
                messages.success(request, f'PQRS actualizado al estado: {pqrs_actualizado.get_estado_display()}.')
            
            # 3. Handle Internal Note
            nota_interna = form.cleaned_data.get('nota_interna')
            if action == 'save_internal_note':
                if not nota_interna:
                    messages.error(request, 'Debe proporcionar contenido para la nota interna.')
                    return redirect('pqrs:pqrs_detail', pk=pk)
                # The note is saved in the form, but we just need to create the event
                PqrsEvento.objects.create(
                    pqrs=pqrs_actualizado,
                    usuario=request.user,
                    tipo_evento=PqrsEvento.EVENTO_NOTA,
                    comentario=nota_interna
                )
                messages.success(request, 'Nota interna guardada exitosamente.')

        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")

    return redirect(reverse('pqrs:pqrs_detail', kwargs={'pk': pk}))


@never_cache
@login_required
@require_POST
@check_user_role(allowed_roles=['Administrador'])
def pqrs_delete(request, pk):
    pqrs = get_object_or_404(Pqrs, pk=pk)
    pqrs.delete()
    return JsonResponse({'message': 'PQRS eliminado exitosamente.'})