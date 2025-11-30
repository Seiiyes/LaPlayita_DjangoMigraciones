/**
 * RECEPCIÓN DE MERCANCÍA - VERSIÓN MEJORADA
 * - Drawer lateral en lugar de fullscreen
 * - Guardado automático de borrador
 * - Validación en vivo por fila
 * - Auditoría automática
 * - Búsqueda en vivo
 * - Mejor UX en móvil
 */

class ReceptionManager {
    constructor() {
        this.currentReceptionData = null;
        this.validationState = new Map();
        this.draftData = new Map();
        this.init();
    }

    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupEventListeners());
        } else {
            this.setupEventListeners();
        }
    }

    setupEventListeners() {
        // Botones principales
        document.getElementById('markAllReceivedBtn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.markAllReceived();
        });

        document.getElementById('applyGeneralExpiryBtn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.applyGeneralExpiry();
        });

        document.getElementById('saveDraftBtn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.saveDraft();
        });

        document.getElementById('confirmReceptionBtn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.confirmReception();
        });

        document.getElementById('cancelReceptionBtn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.exitReceptionMode();
        });

        document.getElementById('closeReceptionDrawer')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.exitReceptionMode();
        });

        document.getElementById('clearSearchBtn')?.addEventListener('click', (e) => {
            e.preventDefault();
            document.getElementById('searchProductInput').value = '';
            this.filterTableBySearch('');
        });

        document.getElementById('searchProductInput')?.addEventListener('keyup', (e) => {
            this.filterTableBySearch(e.target.value);
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (!this.currentReceptionData) return;
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.confirmReception();
            }
            if (e.key === 'Escape') {
                e.preventDefault();
                this.exitReceptionMode();
            }
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                this.saveDraft();
            }
        });

        // Auto-save cada 30 segundos
        setInterval(() => {
            if (this.currentReceptionData) {
                this.autoSaveDraft();
            }
        }, 30000);
    }

    enterReceptionMode(reabastecimientoData) {
        this.currentReceptionData = reabastecimientoData;
        this.validationState.clear();

        console.log('Datos de reabastecimiento recibidos:', reabastecimientoData);
        console.log('Detalles originales:', reabastecimientoData.detalles);

        // Guardar detalles originales ANTES de cargar borrador
        const detallesOriginales = JSON.parse(JSON.stringify(reabastecimientoData.detalles || []));

        // Cargar borrador si existe (solo para valores de cantidad, fecha, lote)
        const draftKey = `draft_${reabastecimientoData.id}`;
        const savedDraft = localStorage.getItem(draftKey);
        if (savedDraft) {
            try {
                const draft = JSON.parse(savedDraft);
                // Fusionar borrador con detalles originales
                detallesOriginales.forEach(detalle => {
                    const draftDetalle = draft.detalles.find(d => d.id === detalle.id);
                    if (draftDetalle) {
                        detalle.cantidad_recibida = draftDetalle.cantidad_recibida;
                        detalle.fecha_caducidad = draftDetalle.fecha_caducidad;
                        detalle.numero_lote = draftDetalle.numero_lote;
                    }
                });
                this.showToast('Borrador cargado', 'info');
            } catch (e) {
                console.error('Error cargando borrador:', e);
            }
        }

        // Actualizar header
        document.getElementById('receptionOrderId').textContent = reabastecimientoData.id;
        document.getElementById('receptionProveedorName').textContent = reabastecimientoData.proveedor_nombre || 'N/A';

        // Poblar tabla con detalles completos
        console.log('Detalles a poblar:', detallesOriginales);
        this.populateReceptionTable(detallesOriginales);

        // Mostrar drawer
        const drawer = new bootstrap.Offcanvas(document.getElementById('receptionDrawer'));
        drawer.show();

        // Actualizar progreso
        this.updateProgress();
    }

    exitReceptionMode() {
        const drawer = bootstrap.Offcanvas.getInstance(document.getElementById('receptionDrawer'));
        if (drawer) {
            drawer.hide();
        }

        this.currentReceptionData = null;
        this.validationState.clear();
        document.getElementById('receptionTableBody').innerHTML = '';
        document.getElementById('searchProductInput').value = '';
    }

    populateReceptionTable(detalles) {
        const tbody = document.getElementById('receptionTableBody');
        tbody.innerHTML = '';

        detalles.forEach((detalle, index) => {
            const row = this.createReceptionRow(detalle, index);
            tbody.appendChild(row);
        });

        this.updateProgress();
    }

    createReceptionRow(detalle, index) {
        const row = document.createElement('tr');
        row.dataset.detalleId = detalle.id;
        row.dataset.index = index;

        console.log('Detalle recibido:', detalle);
        const quantityRecibida = detalle.cantidad_recibida || 0;
        const cantidad = detalle.cantidad || 0;
        const status = this.getRowStatus(quantityRecibida, cantidad);

        row.innerHTML = `
            <td>
                <span class="status-dot" data-status="${status}"></span>
                <small class="fw-500">${detalle.producto_nombre}</small>
            </td>
            <td class="text-center">
                <small class="text-muted">${cantidad}</small>
            </td>
            <td class="text-center">
                <input type="number" 
                       name="cantidad_${detalle.id}"
                       class="form-control form-control-sm reception-quantity-input" 
                       data-detalle-id="${detalle.id}"
                       data-solicitado="${cantidad}"
                       value="${quantityRecibida}"
                       min="0"
                       max="${cantidad}"
                       placeholder="0">
            </td>
            <td class="text-center">
                <input type="date" 
                       name="fecha_${detalle.id}"
                       class="form-control form-control-sm reception-expiry-input" 
                       data-detalle-id="${detalle.id}"
                       value="${detalle.fecha_caducidad || ''}">
            </td>
            <td class="text-center">
                <input type="text" 
                       name="lote_${detalle.id}"
                       class="form-control form-control-sm reception-lote-input" 
                       data-detalle-id="${detalle.id}"
                       value="${detalle.numero_lote || ''}"
                       placeholder="Lote/Serial">
            </td>
            <td class="text-center">
                <span class="badge" id="status-${detalle.id}">
                    ${this.getStatusBadge(status)}
                </span>
            </td>
        `;

        // Event listeners para validación en vivo
        const quantityInput = row.querySelector('.reception-quantity-input');
        const expiryInput = row.querySelector('.reception-expiry-input');
        const loteInput = row.querySelector('.reception-lote-input');

        quantityInput.addEventListener('change', () => {
            this.validateRow(detalle.id, row);
            this.updateProgress();
        });

        expiryInput.addEventListener('change', () => {
            this.validateRow(detalle.id, row);
            this.updateProgress();
        });

        loteInput.addEventListener('change', () => {
            this.validateRow(detalle.id, row);
        });

        return row;
    }

    validateRow(detalleId, row) {
        const quantityInput = row.querySelector('.reception-quantity-input');
        const expiryInput = row.querySelector('.reception-expiry-input');
        const statusBadge = document.getElementById(`status-${detalleId}`);

        const quantity = parseInt(quantityInput.value) || 0;
        const solicitado = parseInt(quantityInput.dataset.solicitado);
        const expiry = expiryInput.value;

        let isValid = true;
        let status = 'pending';

        // Validar cantidad
        if (quantity > solicitado) {
            quantityInput.classList.add('is-invalid');
            quantityInput.classList.remove('is-valid');
            isValid = false;
        } else if (quantity === solicitado) {
            quantityInput.classList.add('is-valid');
            quantityInput.classList.remove('is-invalid');
            status = 'complete';
        } else if (quantity > 0) {
            quantityInput.classList.add('is-valid');
            quantityInput.classList.remove('is-invalid');
            status = 'partial';
        } else {
            quantityInput.classList.remove('is-valid', 'is-invalid');
            status = 'pending';
        }

        // Validar fecha si hay cantidad
        if (quantity > 0 && !expiry) {
            expiryInput.classList.add('is-invalid');
            isValid = false;
        } else if (quantity > 0 && expiry) {
            expiryInput.classList.add('is-valid');
            expiryInput.classList.remove('is-invalid');
        } else {
            expiryInput.classList.remove('is-valid', 'is-invalid');
        }

        // Actualizar estado visual de la fila
        row.classList.remove('row-complete', 'row-partial', 'row-pending');
        row.classList.add(`row-${status}`);

        // Actualizar badge
        const statusDot = row.querySelector('.status-dot');
        statusDot.dataset.status = status;
        statusBadge.innerHTML = this.getStatusBadge(status);

        this.validationState.set(detalleId, { isValid, status, quantity, expiry });
        this.updateConfirmButton();

        return isValid;
    }

    getRowStatus(quantity, solicitado) {
        if (quantity === 0) return 'pending';
        if (quantity === solicitado) return 'complete';
        return 'partial';
    }

    getStatusBadge(status) {
        const badges = {
            complete: '<i class="fas fa-check-circle"></i> Completo',
            partial: '<i class="fas fa-exclamation-circle"></i> Parcial',
            pending: '<i class="fas fa-clock"></i> Pendiente'
        };
        return badges[status] || badges.pending;
    }

    updateProgress() {
        if (!this.currentReceptionData) return;

        let completed = 0;
        let partial = 0;
        let pending = 0;

        this.validationState.forEach(({ status }) => {
            if (status === 'complete') completed++;
            else if (status === 'partial') partial++;
            else pending++;
        });

        const total = completed + partial + pending;
        const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

        document.getElementById('completedCount').textContent = completed;
        document.getElementById('partialCount').textContent = partial;
        document.getElementById('pendingCount').textContent = pending;
        document.getElementById('progressText').textContent = `${completed + partial} de ${total}`;
        document.getElementById('progressBar').style.width = `${percentage}%`;
        document.getElementById('progressBar').setAttribute('aria-valuenow', percentage);
    }

    updateConfirmButton() {
        const confirmBtn = document.getElementById('confirmReceptionBtn');
        const hasAtLeastOne = Array.from(this.validationState.values()).some(
            v => v.quantity > 0
        );
        confirmBtn.disabled = !hasAtLeastOne;
    }

    markAllReceived() {
        const rows = document.querySelectorAll('#receptionTableBody tr');
        rows.forEach(row => {
            const quantityInput = row.querySelector('.reception-quantity-input');
            const solicitado = parseInt(quantityInput.dataset.solicitado);
            quantityInput.value = solicitado;
            quantityInput.dispatchEvent(new Event('change'));
        });
        this.showToast('Todos marcados como recibidos', 'success');
    }

    applyGeneralExpiry() {
        const date = document.getElementById('generalExpiryDate').value;
        if (!date) {
            this.showToast('Selecciona una fecha primero', 'warning');
            return;
        }

        const rows = document.querySelectorAll('#receptionTableBody tr');
        rows.forEach(row => {
            const expiryInput = row.querySelector('.reception-expiry-input');
            expiryInput.value = date;
            expiryInput.dispatchEvent(new Event('change'));
        });
        this.showToast(`Fecha ${date} aplicada a todos`, 'success');
    }

    filterTableBySearch(query) {
        const rows = document.querySelectorAll('#receptionTableBody tr');
        const lowerQuery = query.toLowerCase();

        rows.forEach(row => {
            const productName = row.querySelector('td:first-child small').textContent.toLowerCase();
            const matches = productName.includes(lowerQuery);
            row.classList.toggle('row-hidden', !matches);
        });
    }

    saveDraft() {
        if (!this.currentReceptionData) return;

        const detalles = [];
        document.querySelectorAll('#receptionTableBody tr').forEach(row => {
            const detalleId = row.dataset.detalleId;
            const quantity = parseInt(row.querySelector('.reception-quantity-input').value) || 0;
            const expiry = row.querySelector('.reception-expiry-input').value;
            const lote = row.querySelector('.reception-lote-input').value;

            detalles.push({
                id: detalleId,
                cantidad_recibida: quantity,
                fecha_caducidad: expiry,
                numero_lote: lote
            });
        });

        const draftKey = `draft_${this.currentReceptionData.id}`;
        localStorage.setItem(draftKey, JSON.stringify({ detalles }));
        this.showToast('Borrador guardado', 'success');
    }

    autoSaveDraft() {
        if (!this.currentReceptionData) return;

        const detalles = [];
        document.querySelectorAll('#receptionTableBody tr').forEach(row => {
            const detalleId = row.dataset.detalleId;
            const quantity = parseInt(row.querySelector('.reception-quantity-input').value) || 0;
            const expiry = row.querySelector('.reception-expiry-input').value;
            const lote = row.querySelector('.reception-lote-input').value;

            detalles.push({
                id: detalleId,
                cantidad_recibida: quantity,
                fecha_caducidad: expiry,
                numero_lote: lote
            });
        });

        const draftKey = `draft_${this.currentReceptionData.id}`;
        localStorage.setItem(draftKey, JSON.stringify({ detalles }));
    }

    confirmReception() {
        if (!this.currentReceptionData) return;

        // Validar que al menos un producto esté completo o parcial
        const hasValidItems = Array.from(this.validationState.values()).some(
            v => v.quantity > 0
        );

        if (!hasValidItems) {
            this.showToast('Debes recibir al menos 1 producto', 'warning');
            return;
        }

        // Recopilar datos
        const detalles = [];
        document.querySelectorAll('#receptionTableBody tr').forEach(row => {
            const detalleId = row.dataset.detalleId;
            const quantity = parseInt(row.querySelector('.reception-quantity-input').value) || 0;
            const expiry = row.querySelector('.reception-expiry-input').value;
            const lote = row.querySelector('.reception-lote-input').value;

            if (quantity > 0) {
                detalles.push({
                    id: detalleId,
                    cantidad_recibida: quantity,
                    fecha_caducidad: expiry,
                    numero_lote: lote
                });
            }
        });

        console.log('Datos a enviar:', { detalles });

        // Enviar al servidor
        const container = document.getElementById('reabastecimiento-container');
        const url = container.dataset.recibirUrl.replace('0', this.currentReceptionData.id);

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({ detalles })
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    this.showToast(data.error, 'danger');
                } else {
                    this.showToast('Recepción confirmada', 'success');
                    
                    // Limpiar borrador
                    const draftKey = `draft_${this.currentReceptionData.id}`;
                    localStorage.removeItem(draftKey);

                    // Cerrar drawer y recargar tabla
                    setTimeout(() => {
                        this.exitReceptionMode();
                        location.reload();
                    }, 1500);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                this.showToast('Error al confirmar recepción', 'danger');
            });
    }

    showToast(message, type = 'info') {
        const toastContainer = document.querySelector('.toast-container');
        const toastId = `toast-${Date.now()}`;

        const toastHTML = `
            <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-body bg-${type} text-white">
                    ${message}
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();

        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
               document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] ||
               '';
    }
}

// Inicializar
const receptionManager = new ReceptionManager();

// Exportar para uso global
window.receptionManager = receptionManager;
