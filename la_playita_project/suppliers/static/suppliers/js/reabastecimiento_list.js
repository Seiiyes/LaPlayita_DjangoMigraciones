/**
 * LISTA DE REABASTECIMIENTO - MEJORADA
 * - Flujo simplificado
 * - Mejor validación
 * - Auditoría
 */

document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('reabastecimiento-container');
    const ELIMINAR_URL = container.dataset.eliminarUrl;
    const PROVEEDORES_SEARCH_URL = container.dataset.proveedoresSearchUrl;

    // ===== CONTADORES DE ÓRDENES =====
    function updateCounters() {
        const solicitados = document.querySelectorAll('tr.reabastecimiento-row').length - 
                           document.querySelectorAll('tr[data-estado="recibido"]').length - 
                           document.querySelectorAll('tr[data-estado="cancelado"]').length;
        const recibidos = document.querySelectorAll('tr[data-estado="recibido"]').length;
        const cancelados = document.querySelectorAll('tr[data-estado="cancelado"]').length;
        
        const countSolicitado = document.getElementById('count-solicitado');
        const countRecibido = document.getElementById('count-recibido');
        const countCancelado = document.getElementById('count-cancelado');
        
        if (countSolicitado) countSolicitado.textContent = Math.max(0, solicitados);
        if (countRecibido) countRecibido.textContent = recibidos;
        if (countCancelado) countCancelado.textContent = cancelados;
    }
    
    updateCounters();
    
    const tableBody = document.getElementById('reabastecimiento-list-body');
    if (tableBody) {
        const observer = new MutationObserver(updateCounters);
        observer.observe(tableBody, { childList: true, subtree: true });
    }

    // ===== FILTROS CON DEBOUNCE =====
    let proveedorTimeout;

    const filterProveedor = document.getElementById('filter_proveedor');
    if (filterProveedor) {
        filterProveedor.addEventListener('input', function() {
            clearTimeout(proveedorTimeout);
            const query = this.value.trim();
            const suggestionsDiv = document.getElementById('proveedor_suggestions');
            
            if (query.length < 2) {
                suggestionsDiv.style.display = 'none';
                this.classList.remove('is-loading');
                return;
            }
            
            this.classList.add('is-loading');
            suggestionsDiv.innerHTML = '<div class="list-group-item text-muted"><small><i class="fas fa-spinner fa-spin me-2"></i>Buscando...</small></div>';
            suggestionsDiv.style.display = 'block';
            
            proveedorTimeout = setTimeout(async () => {
                try {
                    const response = await fetch(`${PROVEEDORES_SEARCH_URL}?q=${encodeURIComponent(query)}`);
                    const data = await response.json();
                    
                    if (data.results.length === 0) {
                        suggestionsDiv.innerHTML = '<div class="list-group-item text-muted"><small><i class="fas fa-search me-2"></i>No encontrado</small></div>';
                    } else {
                        suggestionsDiv.innerHTML = data.results.map(r => 
                            `<button type="button" class="list-group-item list-group-item-action" data-id="${r.id}" data-text="${r.text}">
                                <i class="fas fa-building me-2 text-primary"></i>${r.text}
                            </button>`
                        ).join('');
                        
                        suggestionsDiv.querySelectorAll('button').forEach(btn => {
                            btn.addEventListener('click', (e) => {
                                e.preventDefault();
                                document.getElementById('filter_proveedor').value = btn.dataset.text;
                                document.getElementById('filter_proveedor_id').value = btn.dataset.id;
                                suggestionsDiv.style.display = 'none';
                                filterProveedor.classList.remove('is-loading');
                            });
                        });
                    }
                    suggestionsDiv.style.display = 'block';
                } catch (error) {
                    console.error('Error fetching proveedores:', error);
                    suggestionsDiv.innerHTML = '<div class="list-group-item text-danger"><small><i class="fas fa-exclamation-circle me-2"></i>Error en búsqueda</small></div>';
                } finally {
                    filterProveedor.classList.remove('is-loading');
                }
            }, 150);
        });
    }

    // Cerrar sugerencias al hacer click fuera
    document.addEventListener('click', function(e) {
        const proveedorSuggestions = document.getElementById('proveedor_suggestions');
        
        if (proveedorSuggestions && !e.target.closest('#filter_proveedor') && !e.target.closest('#proveedor_suggestions')) {
            proveedorSuggestions.style.display = 'none';
        }
    });

    // ===== TOAST NOTIFICATIONS =====
    function showToast(message, type = 'success', duration = 3000) {
        const toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            console.log(`[${type.toUpperCase()}] ${message}`);
            return;
        }
        
        const toastId = `toast-${Date.now()}`;
        const bgClass = `bg-${type}`;
        const closeButtonClass = type === 'warning' ? 'btn-close' : 'btn-close-white';
        
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="${duration}">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="fas fa-check-circle me-2"></i>${message}
                    </div>
                    <button type="button" class="${closeButtonClass} me-2 m-auto" data-bs-dismiss="toast" aria-label="Cerrar"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = document.getElementById(toastId);
        
        try {
            const toast = new bootstrap.Toast(toastElement, { delay: duration });
            toast.show();
            
            toastElement.addEventListener('hidden.bs.toast', function () {
                toastElement.remove();
            });
        } catch (error) {
            console.error('Error showing toast:', error);
            toastElement.remove();
        }
    }

    window.showToast = showToast;

    // ===== GLOBAL FUNCTIONS =====
    window.recibirReabastecimiento = async function(id) {
        try {
            const detailApiUrl = `/suppliers/reabastecimientos/${id}/details_api/`;
            const response = await fetch(detailApiUrl);
            if (!response.ok) throw new Error('Error al cargar datos: ' + response.status);
            
            const data = await response.json();
            
            if (window.receptionManager) {
                window.receptionManager.enterReceptionMode(data);
            } else {
                console.error('ReceptionManager no está disponible');
                showToast('Error: Módulo de recepción no cargado', 'danger');
            }
        } catch (error) {
            console.error('Error en recibirReabastecimiento:', error);
            showToast(error.message, 'danger');
        }
    };

    window.editarReabastecimiento = async function(id) {
        const editarLoadingSpinner = document.getElementById('editarLoadingSpinner');
        if (editarLoadingSpinner) {
            editarLoadingSpinner.style.display = 'flex';
        }
        
        try {
            const detailApiUrl = `/suppliers/reabastecimientos/${id}/details_api/`;
            const response = await fetch(detailApiUrl);
            if (!response.ok) throw new Error('Error al cargar');
            
            const data = await response.json();
            
            const formasPago = [
                { value: 'transferencia', text: 'Transferencia Bancaria' },
                { value: 'efectivo', text: 'Efectivo' },
                { value: 'cheque', text: 'Cheque' },
                { value: 'pse', text: 'PSE' },
                { value: 'tarjeta_credito', text: 'Tarjeta de Crédito' },
                { value: 'consignacion', text: 'Consignación Bancaria' }
            ];
            
            const editarModalContent = document.getElementById('editarModalContent');
            if (!editarModalContent) {
                throw new Error('Modal no encontrado en el DOM');
            }
            
            editarModalContent.innerHTML = `
                <form id="editarReabastecimientoForm" data-reabastecimiento-id="${data.id}">
                    <input type="hidden" id="editarReabastecimientoId" value="${data.id}">
                    
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label for="proveedor_edit" class="form-label">Proveedor</label>
                            <input type="text" class="form-control" id="proveedor_edit" value="${data.proveedor_id}" disabled>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label for="estado_edit" class="form-label">Estado</label>
                            <input type="text" class="form-control" id="estado_edit" value="${data.estado}" disabled>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label for="fecha_edit" class="form-label">Fecha Solicitud</label>
                            <input type="datetime-local" class="form-control" id="fecha_edit" value="${data.fecha ? new Date(data.fecha).toISOString().slice(0, 16) : ''}" disabled>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label for="forma_pago_edit" class="form-label">Forma de Pago</label>
                            <select class="form-select" id="forma_pago_edit" name="forma_pago">
                                ${formasPago.map(fp => `<option value="${fp.value}" ${data.forma_pago === fp.value ? 'selected' : ''}>${fp.text}</option>`).join('')}
                            </select>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label for="costo_total_edit" class="form-label">Costo Total</label>
                            <input type="number" class="form-control" id="costo_total_edit" value="${data.costo_total}" disabled step="0.01">
                        </div>
                        <div class="col-md-6 mb-3">
                            <label for="iva_edit" class="form-label">IVA Total</label>
                            <input type="number" class="form-control" id="iva_edit" value="${data.iva}" disabled step="0.01">
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label for="observaciones_edit" class="form-label">Observaciones</label>
                        <textarea class="form-control" id="observaciones_edit" name="observaciones" rows="3">${data.observaciones || ''}</textarea>
                    </div>
                    
                    <div class="alert alert-info alert-sm" role="alert">
                        <small><i class="fas fa-info-circle me-2"></i>Solo puedes editar la forma de pago y observaciones.</small>
                    </div>
                </form>
            `;
            
            setTimeout(() => {
                const modalElement = document.getElementById('editarReabastecimientoModal');
                if (modalElement) {
                    try {
                        const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
                        modal.show();
                    } catch (e) {
                        console.error('Error al mostrar modal:', e);
                        showToast('Error al abrir el formulario de edición', 'danger');
                    }
                }
            }, 100);
        } catch (error) {
            console.error('Error:', error);
            showToast(error.message, 'danger');
        } finally {
            if (editarLoadingSpinner) {
                editarLoadingSpinner.style.display = 'none';
            }
        }
    };

    window.eliminarReabastecimiento = async function(id) {
        const result = await Swal.fire({
            title: '¿Estás seguro?',
            text: "¡No podrás revertir esto!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Sí, eliminarlo',
            cancelButtonText: 'Cancelar',
            allowOutsideClick: false,
            allowEscapeKey: false
        });
        
        if (!result.isConfirmed) return;
        
        try {
            const response = await fetch(ELIMINAR_URL.replace('0', id), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });
            
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Error al eliminar');
            }
            
            const row = document.getElementById(`reabastecimiento-row-${id}`);
            if (row) {
                row.style.animation = 'fadeOut 0.3s ease-out';
                setTimeout(() => row.remove(), 300);
            }
            
            updateCounters();
            showToast('Reabastecimiento eliminado correctamente', 'success');
        } catch (error) {
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: error.message
            });
        }
    };

    window.verDetallesReabastecimiento = async function(id) {
        try {
            const detailApiUrl = `/suppliers/reabastecimientos/${id}/details_api/`;
            console.log('Llamando a API:', detailApiUrl);
            const response = await fetch(detailApiUrl);
            if (!response.ok) throw new Error('Error al cargar detalles: ' + response.status);
            
            const data = await response.json();
            console.log('Datos recibidos:', data);
            console.log('Detalles:', data.detalles);
            const fecha = new Date(data.fecha).toLocaleDateString('es-CO', {year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'});
            
            let html = `
                <div class="detalles-reabastecimiento" style="text-align: left;">
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <small class="text-muted d-block">Proveedor</small>
                            <p class="fw-bold mb-0">${data.proveedor_nombre}</p>
                        </div>
                        <div class="col-md-6">
                            <small class="text-muted d-block">Estado</small>
                            <p class="mb-0">
                                <span class="badge ${data.estado === 'recibido' ? 'bg-success' : data.estado === 'solicitado' ? 'bg-warning text-dark' : 'bg-danger'}">
                                    ${data.estado === 'solicitado' ? 'Solicitado' : data.estado === 'recibido' ? 'Recibido' : 'Cancelado'}
                                </span>
                            </p>
                        </div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <small class="text-muted d-block">Fecha</small>
                            <p class="fw-bold mb-0">${fecha}</p>
                        </div>
                        <div class="col-md-6">
                            <small class="text-muted d-block">Forma de Pago</small>
                            <p class="fw-bold mb-0">${data.forma_pago.replace(/_/g, ' ').toUpperCase()}</p>
                        </div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <small class="text-muted d-block">Subtotal</small>
                            <p class="fw-bold mb-0">$${(parseFloat(data.costo_total) - parseFloat(data.iva)).toLocaleString('es-CO', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
                        </div>
                        <div class="col-md-6">
                            <small class="text-muted d-block">IVA</small>
                            <p class="fw-bold mb-0">$${parseFloat(data.iva).toLocaleString('es-CO', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
                        </div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-12">
                            <small class="text-muted d-block">Total</small>
                            <p class="fw-bold mb-0 fs-5">$${parseFloat(data.costo_total).toLocaleString('es-CO', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
                        </div>
                    </div>
                    ${data.observaciones ? `
                        <div class="mb-3">
                            <small class="text-muted d-block">Observaciones</small>
                            <p class="mb-0">${data.observaciones}</p>
                        </div>
                    ` : ''}
                    <hr>
                    <h6 class="mb-3">Productos (${data.detalles && data.detalles.length > 0 ? data.detalles.length : 0})</h6>
                    ${data.detalles && data.detalles.length > 0 ? `
                        <div class="table-responsive">
                            <table class="table table-sm table-bordered">
                                <thead class="table-light">
                                    <tr>
                                        <th>Producto</th>
                                        <th class="text-center">Solicitado</th>
                                        <th class="text-center">Recibido</th>
                                        <th class="text-center">Costo Unit.</th>
                                        <th class="text-center">Caducidad</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${data.detalles.map(d => {
                                        const estado = d.cantidad_recibida === d.cantidad ? 'table-success' : d.cantidad_recibida > 0 ? 'table-warning' : '';
                                        return `
                                            <tr class="${estado}">
                                                <td>${d.producto_nombre || 'Sin nombre'}</td>
                                                <td class="text-center">${d.cantidad || 0}</td>
                                                <td class="text-center fw-bold">${d.cantidad_recibida || 0}</td>
                                                <td class="text-center">$${parseFloat(d.costo_unitario || 0).toLocaleString('es-CO', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                                                <td class="text-center">${d.fecha_caducidad ? new Date(d.fecha_caducidad).toLocaleDateString('es-CO') : '-'}</td>
                                            </tr>
                                        `;
                                    }).join('')}
                                </tbody>
                            </table>
                        </div>
                    ` : `
                        <div class="alert alert-info">
                            <small>No hay productos en este reabastecimiento</small>
                        </div>
                    `}
                </div>
            `;
            
            Swal.fire({
                title: `Detalles - Orden #${id}`,
                html: html,
                icon: 'info',
                width: '800px',
                confirmButtonText: 'Cerrar'
            });
        } catch (error) {
            console.error('Error:', error);
            showToast('Error al cargar detalles', 'danger');
        }
    };

    window.verAuditoria = async function(id) {
        try {
            const response = await fetch(`/suppliers/reabastecimientos/${id}/audit_history/`);
            if (!response.ok) throw new Error('Error al cargar auditoría');
            
            const data = await response.json();
            
            let html = '<div class="audit-history">';
            if (data.auditorias.length === 0) {
                html += '<p class="text-muted text-center py-3">Sin cambios registrados</p>';
            } else {
                html += '<div class="timeline">';
                data.auditorias.forEach(audit => {
                    const fecha = new Date(audit.fecha).toLocaleString('es-CO');
                    html += `
                        <div class="timeline-item mb-3 pb-3 border-bottom">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <span class="badge bg-primary">${audit.accion}</span>
                                    <small class="text-muted d-block mt-1">
                                        <i class="fas fa-user me-1"></i>${audit.usuario}
                                    </small>
                                </div>
                                <small class="text-muted">${fecha}</small>
                            </div>
                            <p class="mt-2 mb-0 text-sm">${audit.descripcion || '-'}</p>
                            ${audit.cantidad_anterior !== null ? `<small class="text-muted d-block mt-1">Cantidad: ${audit.cantidad_anterior} → ${audit.cantidad_nueva}</small>` : ''}
                        </div>
                    `;
                });
                html += '</div>';
            }
            html += '</div>';
            
            Swal.fire({
                title: `Historial - Orden #${id}`,
                html: html,
                icon: 'info',
                width: '600px',
                confirmButtonText: 'Cerrar'
            });
        } catch (error) {
            console.error('Error:', error);
            showToast('Error al cargar historial de auditoría', 'danger');
        }
    };

    // ===== ROW CLICK HANDLERS =====
    function attachRowClickListener(row) {
        const btnRecibir = row.querySelector('.btn-recibir');
        if (btnRecibir) {
            btnRecibir.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const id = btnRecibir.dataset.id;
                recibirReabastecimiento(id);
            });
        }
        
        const btnEditar = row.querySelector('.btn-editar');
        if (btnEditar) {
            btnEditar.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const id = btnEditar.dataset.id;
                editarReabastecimiento(id);
            });
        }
        
        const btnEliminar = row.querySelector('.btn-eliminar');
        if (btnEliminar) {
            btnEliminar.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const id = btnEliminar.dataset.id;
                eliminarReabastecimiento(id);
            });
        }

        const btnAuditoria = row.querySelector('.btn-ver-auditoria');
        if (btnAuditoria) {
            btnAuditoria.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const id = btnAuditoria.dataset.id;
                verAuditoria(id);
            });
        }

        const btnVerDetalles = row.querySelector('.btn-ver-detalles');
        if (btnVerDetalles) {
            btnVerDetalles.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const id = btnVerDetalles.dataset.id;
                verDetallesReabastecimiento(id);
            });
        }
    }

    // ===== BÚSQUEDA GLOBAL =====
    const globalSearch = document.getElementById('global_search');
    if (globalSearch) {
        globalSearch.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            const rows = document.querySelectorAll('.reabastecimiento-row');
            let visibleCount = 0;
            
            rows.forEach(row => {
                const proveedor = row.querySelector('td:nth-child(1)')?.textContent.toLowerCase() || '';
                const estado = row.dataset.estado || '';
                const rowText = proveedor + ' ' + estado;
                
                const matches = rowText.includes(query);
                row.style.display = matches ? '' : 'none';
                if (matches) visibleCount++;
            });
            
            if (query.length > 0 && visibleCount === 0) {
                globalSearch.classList.add('is-invalid');
            } else {
                globalSearch.classList.remove('is-invalid');
            }
        });
    }

    // Attach listeners a filas existentes
    document.querySelectorAll('.reabastecimiento-row').forEach(row => {
        attachRowClickListener(row);
    });

    window.attachRowClickListener = attachRowClickListener;
});
