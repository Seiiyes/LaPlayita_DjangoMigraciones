/**
 * LISTA DE REABASTECIMIENTO - VERSIÓN MEJORADA
 * - Flujo simplificado con tabs
 * - Modal unificado para recepción
 * - Mejor validación en vivo
 * - Búsqueda y filtros optimizados
 */

document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('reabastecimiento-container');
    const ELIMINAR_URL = container.dataset.eliminarUrl;
    const PROVEEDORES_SEARCH_URL = container.dataset.proveedoresSearchUrl;

    // ===== MOSTRAR MENSAJE DE ÉXITO SI VIENE DE EDICIÓN =====
    const successData = sessionStorage.getItem('successMessage');
    if (successData) {
        try {
            const data = JSON.parse(successData);
            sessionStorage.removeItem('successMessage');
            
            const formatCurrency = (value) => {
                return new Intl.NumberFormat('es-CO', {
                    style: 'currency',
                    currency: 'COP',
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0
                }).format(value);
            };
            
            const toastContainer = document.querySelector('.toast-container');
            if (toastContainer) {
                const toastId = `toast-${Date.now()}`;
                const toastHtml = `
                    <div id="${toastId}" class="toast align-items-center text-white bg-success border-0" role="alert">
                        <div class="d-flex">
                            <div class="toast-body">
                                <i class="fas fa-check-circle me-2"></i>
                                <strong>${data.title}</strong><br>
                                ${data.message}<br>
                                <small class="text-white-50">Proveedor: ${data.proveedor} | Total: ${formatCurrency(data.total)}</small>
                            </div>
                            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                        </div>
                    </div>
                `;
                toastContainer.insertAdjacentHTML('beforeend', toastHtml);
                const toastElement = document.getElementById(toastId);
                const toast = new bootstrap.Toast(toastElement, { delay: 2000 });
                toast.show();
            }
        } catch (e) {
            console.error('Error al procesar mensaje de éxito:', e);
        }
    }

    // ===== FILTROS =====
    const applyFiltersBtn = document.getElementById('applyFiltersBtn');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', function() {
            const fechaDesde = document.getElementById('fecha_desde').value;
            const fechaHasta = document.getElementById('fecha_hasta').value;
            const proveedorId = document.getElementById('filter_proveedor_id').value;
            
            let url = '/suppliers/reabastecimientos/?';
            const params = [];
            
            if (fechaDesde) params.push(`fecha_desde=${fechaDesde}`);
            if (fechaHasta) params.push(`fecha_hasta=${fechaHasta}`);
            if (proveedorId) params.push(`proveedor_id=${proveedorId}`);
            
            if (params.length > 0) {
                url += params.join('&');
            }
            
            window.location.href = url;
        });
    }

    // ===== TAB MANAGEMENT =====
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            
            // Remove active class from all
            tabButtons.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked
            this.classList.add('active');
            document.getElementById(`tab-${tabName}`).classList.add('active');
            
            // Populate tab content
            populateTab(tabName);
        });
    });

    function populateTab(tabName) {
        const container = document.getElementById(`${tabName}-list`);
        const reabastecimientos = document.querySelectorAll('[data-reabastecimiento-id]');
        
        let html = '';
        let count = 0;

        reabastecimientos.forEach(row => {
            const estado = row.dataset.estado;
            const shouldShow = (tabName === 'pendientes' && (estado === 'borrador' || estado === 'solicitado')) ||
                              (tabName === 'historial' && (estado === 'recibido' || estado === 'cancelado'));
            
            if (shouldShow) {
                count++;
                const id = row.dataset.reabastecimientoId;
                const proveedor = row.dataset.proveedor || 'N/A';
                const fecha = row.dataset.fecha || '';
                const costoRaw = parseFloat(row.dataset.costo) || 0;
                const ivaRaw = parseFloat(row.dataset.iva) || 0;
                const totalReal = costoRaw + ivaRaw;
                
                const formatCurrency = (value) => {
                    return new Intl.NumberFormat('es-CO', {
                        style: 'currency',
                        currency: 'COP',
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 0
                    }).format(value);
                };
                
                const subtotal = formatCurrency(costoRaw);
                const iva = formatCurrency(ivaRaw);
                const total = formatCurrency(totalReal);
                const ivaPorcentaje = costoRaw > 0 ? ((ivaRaw / costoRaw) * 100).toFixed(2) : 0;
                const productCount = row.dataset.productCount || '0';
                const statusBadge = getStatusBadge(estado);

                html += `
                    <div class="order-card ${estado}" data-order-id="${id}">
                        <div class="row align-items-center">
                            <div class="col-md-6">
                                <h6 class="mb-1">
                                    <strong>Orden #${id}</strong>
                                </h6>
                                <small class="text-muted d-block">
                                    <i class="fas fa-building me-1"></i>${proveedor}
                                </small>
                                <small class="text-muted d-block">
                                    <i class="fas fa-calendar me-1"></i>${fecha}
                                </small>
                            </div>
                            <div class="col-md-3">
                                <div class="text-center">
                                    <small class="text-muted d-block">Productos</small>
                                    <strong class="d-block">${productCount}</strong>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="text-center">
                                    <small class="text-muted d-block" style="font-size: 0.75rem;">Subtotal</small>
                                    <strong class="d-block" style="font-size: 0.9rem; color: #6c757d;">${subtotal}</strong>
                                    <small class="text-muted d-block" style="font-size: 0.75rem;">IVA (${ivaPorcentaje}%): ${iva}</small>
                                    <div style="border-top: 1px solid #dee2e6; margin-top: 0.5rem; padding-top: 0.5rem;">
                                        <small class="text-muted d-block" style="font-size: 0.75rem;">Total</small>
                                        <strong class="d-block text-success">${total}</strong>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="mt-3 pt-3 border-top d-flex gap-2 justify-content-between align-items-center">
                            <div>${statusBadge}</div>
                            <div class="btn-group btn-group-sm" role="group">
                                ${estado === 'borrador' ? `
                                    <button type="button" class="btn btn-primary btn-enviar" data-id="${id}">
                                        <i class="fas fa-paper-plane me-1"></i>Enviar
                                    </button>
                                ` : ''}
                                ${estado === 'solicitado' ? `
                                    <button type="button" class="btn btn-success btn-recibir" data-id="${id}">
                                        <i class="fas fa-truck-loading me-1"></i>Recibir
                                    </button>
                                ` : ''}
                                ${(estado === 'solicitado' || estado === 'borrador') ? `
                                    <button type="button" class="btn btn-outline-primary btn-editar" data-id="${id}">
                                        <i class="fas fa-edit me-1"></i>Editar
                                    </button>
                                ` : ''}
                                <button type="button" class="btn btn-outline-secondary btn-detalles" data-id="${id}">
                                    <i class="fas fa-eye me-1"></i>Ver
                                </button>
                                ${(estado === 'solicitado' || estado === 'borrador') ? `
                                    <button type="button" class="btn btn-outline-danger btn-eliminar" data-id="${id}">
                                        <i class="fas fa-trash me-1"></i>
                                    </button>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                `;
            }
        });

        if (count === 0) {
            html = `
                <div class="text-center py-5">
                    <i class="fas fa-inbox text-muted" style="font-size: 3rem;"></i>
                    <h5 class="text-muted mt-3">No hay órdenes</h5>
                    <p class="text-muted">
                        ${tabName === 'pendientes' ? 'Crea una nueva orden para empezar' : 'No hay historial disponible'}
                    </p>
                </div>
            `;
        }

        container.innerHTML = html;
        updateTabCounts();
        attachEventListeners();
        
        // Ocultar paginación siempre (los datos ya están filtrados en frontend por tabs)
        const paginationNav = document.querySelector('nav[aria-label="Paginación"]');
        if (paginationNav) {
            paginationNav.style.display = 'none';
        }
    }

    function getStatusBadge(estado) {
        const badges = {
            'borrador': '<span class="badge bg-secondary"><i class="fas fa-file me-1"></i>Borrador</span>',
            'solicitado': '<span class="badge bg-warning text-dark"><i class="fas fa-hourglass-half me-1"></i>Solicitado</span>',
            'recibido': '<span class="badge bg-success"><i class="fas fa-check-circle me-1"></i>Recibido</span>',
            'cancelado': '<span class="badge bg-danger"><i class="fas fa-ban me-1"></i>Cancelado</span>'
        };
        return badges[estado] || '<span class="badge bg-secondary">Desconocido</span>';
    }

    function updateTabCounts() {
        const borradores = document.querySelectorAll('[data-estado="borrador"]').length;
        const solicitados = document.querySelectorAll('[data-estado="solicitado"]').length;
        const pendientes = borradores + solicitados;
        const historial = document.querySelectorAll('[data-estado="recibido"], [data-estado="cancelado"]').length;
        
        document.getElementById('count-pendientes').textContent = pendientes;
        document.getElementById('count-historial').textContent = historial;
    }

    // ===== SEARCH & FILTERS =====
    const globalSearch = document.getElementById('global_search');
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    const toggleFiltersBtn = document.getElementById('toggleFiltersBtn');
    const filtersCollapse = document.getElementById('filtersCollapse');

    if (globalSearch) {
        globalSearch.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            clearSearchBtn.style.display = query ? 'block' : 'none';
            
            const rows = document.querySelectorAll('[data-reabastecimiento-id]');
            rows.forEach(row => {
                const id = row.dataset.reabastecimientoId;
                const proveedor = row.dataset.proveedor || '';
                const text = (id + ' ' + proveedor).toLowerCase();
                
                const card = document.querySelector(`[data-order-id="${id}"]`);
                if (card) {
                    card.style.display = text.includes(query) ? '' : 'none';
                }
            });
        });

        clearSearchBtn.addEventListener('click', function() {
            globalSearch.value = '';
            clearSearchBtn.style.display = 'none';
            document.querySelectorAll('[data-order-id]').forEach(card => {
                card.style.display = '';
            });
        });
    }

    if (toggleFiltersBtn) {
        toggleFiltersBtn.addEventListener('click', function() {
            filtersCollapse.classList.toggle('show');
        });
    }

    // ===== EVENT LISTENERS =====
    function attachEventListeners() {
        // Enviar borrador
        document.querySelectorAll('.btn-enviar').forEach(btn => {
            btn.addEventListener('click', async function() {
                const id = this.dataset.id;
                await enviarBorrador(id);
            });
        });
        
        // Recibir orden
        document.querySelectorAll('.btn-recibir').forEach(btn => {
            btn.addEventListener('click', async function() {
                const id = this.dataset.id;
                await openReceptionModal(id);
            });
        });

        // Editar orden
        document.querySelectorAll('.btn-editar').forEach(btn => {
            btn.addEventListener('click', async function() {
                const id = this.dataset.id;
                window.location.href = `/suppliers/reabastecimientos/${id}/editar/`;
            });
        });

        // Ver detalles
        document.querySelectorAll('.btn-detalles').forEach(btn => {
            btn.addEventListener('click', async function() {
                const id = this.dataset.id;
                await showOrderDetails(id);
            });
        });

        // Eliminar
        document.querySelectorAll('.btn-eliminar').forEach(btn => {
            btn.addEventListener('click', async function() {
                const id = this.dataset.id;
                await deleteOrder(id);
            });
        });
    }

    // ===== RECEPTION MODAL =====
    async function openReceptionModal(id) {
        try {
            const response = await fetch(`/suppliers/reabastecimientos/${id}/details_api/`);
            if (!response.ok) throw new Error('Error al cargar datos');
            
            const data = await response.json();
            
            // Populate modal
            const orderIdEl = document.getElementById('receptionOrderId');
            if (orderIdEl) orderIdEl.textContent = id;
            
            // Populate table
            const tbody = document.getElementById('receptionTableBody');
            tbody.innerHTML = data.detalles.map(detalle => {
                // Parsear fecha como local para evitar problemas de zona horaria
                let fechaCaducidad = 'N/A';
                if (detalle.fecha_caducidad) {
                    const [year, month, day] = detalle.fecha_caducidad.split('-');
                    const date = new Date(year, month - 1, day);
                    fechaCaducidad = date.toLocaleDateString('es-CO');
                }
                return `
                <tr data-detalle-id="${detalle.id}">
                    <td>${detalle.producto_nombre}</td>
                    <td class="text-center">${detalle.cantidad}</td>
                    <td class="text-center">
                        <input type="number" class="form-control form-control-sm cantidad-input" 
                               value="${detalle.cantidad_recibida}" min="0" max="${detalle.cantidad}">
                    </td>
                    <td class="text-center"><small>${fechaCaducidad}</small></td>
                </tr>
            `}).join('');

            // Update progress
            updateReceptionProgress();

            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('receptionModal'));
            modal.show();
            
            // Attach input listeners
            const inputs = document.querySelectorAll('#receptionTableBody .cantidad-input');
            if (inputs && inputs.length > 0) {
                inputs.forEach(input => {
                    if (input) {
                        input.addEventListener('input', updateReceptionProgress);
                    }
                });
            }

            // Attach confirm button listener
            const confirmBtn = document.getElementById('confirmReceptionBtn');
            if (confirmBtn) {
                confirmBtn.onclick = () => confirmReception(id);
            }

            updateReceptionProgress();

        } catch (error) {
            showToast(error.message, 'danger');
        }
    }



    function updateReceptionProgress() {
        const rows = document.querySelectorAll('#receptionTableBody tr');
        let completed = 0, partial = 0, pending = 0;

        rows.forEach(row => {
            const solicitado = parseInt(row.querySelector('td:nth-child(2)').textContent) || 0;
            const recibido = parseInt(row.querySelector('.cantidad-input').value) || 0;

            if (recibido === solicitado && solicitado > 0) {
                completed++;
            } else if (recibido > 0 && recibido < solicitado) {
                partial++;
            } else {
                pending++;
            }
        });

        const total = completed + partial + pending;
        const progressText = document.getElementById('progressText');
        const progressBar = document.getElementById('progressBar');
        const confirmBtn = document.getElementById('confirmReceptionBtn');
        const discrepancyAlert = document.getElementById('discrepancyAlert');

        if (progressText) progressText.textContent = `${completed} de ${total}`;
        if (progressBar) progressBar.style.width = `${total > 0 ? (completed / total) * 100 : 0}%`;
        if (confirmBtn) confirmBtn.disabled = (completed + partial) === 0;

        // Show warning if partial
        if (discrepancyAlert) {
            if (partial > 0) {
                discrepancyAlert.style.display = 'block';
                document.getElementById('discrepancyText').textContent = `${partial} producto(s) con cantidad parcial`;
            } else {
                discrepancyAlert.style.display = 'none';
            }
        }
    }

    async function confirmReception() {
        // TODO: Implement reception confirmation
        showToast('Recepción confirmada', 'success');
    }

    // ===== UTILITY FUNCTIONS =====
    async function showOrderDetails(id) {
        try {
            const response = await fetch(`/suppliers/reabastecimientos/${id}/details_api/`);
            if (!response.ok) throw new Error('Error al cargar detalles');
            
            const data = await response.json();
            
            console.log('[VER DETALLES] Datos recibidos de la API:', data);
            console.log('[VER DETALLES] IVA:', data.iva, 'Costo Total:', data.costo_total, 'IVA %:', data.iva_porcentaje);
            console.log('[VER DETALLES] Todas las claves del objeto:', Object.keys(data));
            
            const formatCurrency = (value) => {
                return new Intl.NumberFormat('es-CO', {
                    style: 'currency',
                    currency: 'COP',
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0
                }).format(value);
            };
            
            const subtotal = formatCurrency(parseFloat(data.costo_total) || 0);
            const iva = formatCurrency(parseFloat(data.iva) || 0);
            const totalReal = formatCurrency((parseFloat(data.costo_total) || 0) + (parseFloat(data.iva) || 0));
            const ivaPorcentaje = data.iva_porcentaje || 0;
            
            let html = `
                <div class="row mb-3">
                    <div class="col-md-6">
                        <small class="text-muted">Proveedor</small>
                        <p class="fw-bold">${data.proveedor_nombre}</p>
                    </div>
                    <div class="col-md-6">
                        <small class="text-muted">Estado</small>
                        <p>${getStatusBadge(data.estado)}</p>
                    </div>
                </div>
                <div class="row mb-3">
                    <div class="col-md-4">
                        <small class="text-muted">Subtotal</small>
                        <p class="fw-bold">${subtotal}</p>
                    </div>
                    <div class="col-md-4">
                        <small class="text-muted">IVA (${ivaPorcentaje}%)</small>
                        <p class="fw-bold text-warning">${iva}</p>
                    </div>
                    <div class="col-md-4">
                        <small class="text-muted">Total</small>
                        <p class="fw-bold text-success">${totalReal}</p>
                    </div>
                </div>
                <hr>
                <h6>Productos (${data.detalles.length})</h6>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead class="table-light">
                            <tr>
                                <th>Producto</th>
                                <th class="text-center">Solicitado</th>
                                <th class="text-center">Recibido</th>
                                <th class="text-center">Caducidad</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.detalles.map(d => {
                                // Parsear fecha como local para evitar problemas de zona horaria
                                let fechaCaducidad = 'N/A';
                                if (d.fecha_caducidad) {
                                    const [year, month, day] = d.fecha_caducidad.split('-');
                                    const date = new Date(year, month - 1, day);
                                    fechaCaducidad = date.toLocaleDateString('es-CO');
                                }
                                return `
                                <tr>
                                    <td>${d.producto_nombre}</td>
                                    <td class="text-center">${d.cantidad}</td>
                                    <td class="text-center">${d.cantidad_recibida}</td>
                                    <td class="text-center"><small>${fechaCaducidad}</small></td>
                                </tr>
                            `}).join('')}
                        </tbody>
                    </table>
                </div>
                <hr>
                <div class="d-flex gap-2 justify-content-end">
                    <a href="/suppliers/reabastecimientos/${id}/download/pdf/" 
                       class="btn btn-outline-danger btn-sm" 
                       target="_blank"
                       title="Descargar PDF">
                        <i class="fas fa-file-pdf me-1"></i> Descargar PDF
                    </a>
                    <a href="/suppliers/reabastecimientos/${id}/download/excel/" 
                       class="btn btn-outline-success btn-sm" 
                       target="_blank"
                       title="Descargar Excel">
                        <i class="fas fa-file-excel me-1"></i> Descargar Excel
                    </a>
                </div>
                <div style="display: none;">
                    <table class="table table-sm">
                        <thead class="table-light">
                            <tr>
                                <th>Producto</th>
                                <th class="text-center">Solicitado</th>
                                <th class="text-center">Recibido</th>
                                <th class="text-center">Caducidad</th>
                            </tr>
                        </thead>
                        <tbody>
                    </table>
                </div>
            `;

            Swal.fire({
                title: `Orden #${id}`,
                html: html,
                icon: 'info',
                width: '600px',
                confirmButtonText: 'Cerrar'
            });
        } catch (error) {
            showToast(error.message, 'danger');
        }
    }

    async function enviarBorrador(id) {
        // Mostrar loading inmediatamente
        Swal.fire({
            title: 'Enviando orden...',
            text: 'Por favor espera',
            allowOutsideClick: false,
            allowEscapeKey: false,
            showConfirmButton: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        try {
            const response = await fetch(`/suppliers/reabastecimientos/${id}/enviar-borrador/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Error al enviar');
            }

            // Actualizar la tarjeta en la interfaz
            const card = document.querySelector(`[data-order-id="${id}"]`);
            if (card) {
                const row = document.querySelector(`[data-reabastecimiento-id="${id}"]`);
                if (row) {
                    row.dataset.estado = 'solicitado';
                }
            }
            
            // Recargar la vista actual
            const activeTab = document.querySelector('.tab-btn.active');
            if (activeTab) {
                populateTab(activeTab.dataset.tab);
            }
            
            Swal.fire({
                icon: 'success',
                title: '¡Orden enviada!',
                text: data.message,
                timer: 2000,
                timerProgressBar: true,
                showConfirmButton: false
            });
        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: error.message,
                confirmButtonColor: '#dc3545'
            });
        }
    }
    
    async function deleteOrder(id) {
        const result = await Swal.fire({
            title: '¿Eliminar orden?',
            text: 'Esta acción no se puede deshacer',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        });

        if (!result.isConfirmed) return;

        try {
            const response = await fetch(ELIMINAR_URL.replace('0', id), {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });

            if (!response.ok) throw new Error('Error al eliminar');

            const card = document.querySelector(`[data-order-id="${id}"]`);
            if (card) card.remove();
            
            updateTabCounts();
            showToast('Orden eliminada', 'success');
        } catch (error) {
            showToast(error.message, 'danger');
        }
    }

    function showToast(message, type = 'success') {
        const toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            console.log(`[${type}] ${message}`);
            return;
        }

        const toastId = `toast-${Date.now()}`;
        const bgClass = `bg-${type}`;

        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="fas fa-check-circle me-2"></i>${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
        toast.show();
    }

    // Initialize
    populateTab('pendientes');
});
