// Reabastecimiento Create Form - Versión Ultra Optimizada
// Mejoras: Búsqueda rápida, IVA automático, validación en vivo, copiar filas, predicción de stock

class ReabastecimientoForm {
    constructor() {
        this.form = document.getElementById('reabastecimientoForm');
        this.detalleTable = document.getElementById('detalleTable');
        this.managementForm = document.querySelector('[name="reabastecimientodetalle_set-TOTAL_FORMS"]');
        this.addRowBtn = document.getElementById('add-row-formset');
        this.guardarBtn = document.getElementById('guardarReabastecimientoBtn');
        this.cancelarBtn = document.getElementById('cancelarBtn');
        this.proveedorSelect = document.getElementById('id_proveedor_select');
        
        this.productos = JSON.parse(document.querySelector('script[data-productos]')?.textContent || '[]');
        this.tasasIva = JSON.parse(document.querySelector('script[data-tasas-iva]')?.textContent || '[]');
        this.productMap = new Map(this.productos.map(p => [p.id, p]));
        
        this.init();
    }

    init() {
        this.populateIvaSelects();
        this.setupEventListeners();
        this.validateForm();
        this.calculateTotals();
        this.updateProductCount();
        
        // Setup Tab navigation para filas existentes
        document.querySelectorAll('tr.formset-row').forEach(row => {
            this.setupRowTabNavigation(row);
        });
    }
    
    populateIvaSelects() {
        document.querySelectorAll('.iva-select').forEach(select => {
            // Guardar el valor seleccionado si existe
            const selectedValue = select.value;
            
            // Limpiar opciones manteniendo la primera
            while (select.options.length > 1) select.remove(1);
            
            // Usar this.tasasIva que viene del contexto de Django
            const tasas = this.tasasIva?.length > 0 ? this.tasasIva : [];
            
            tasas.forEach(tasa => {
                const option = document.createElement('option');
                option.value = tasa.id; // Usar el ID de la tasa como valor
                option.textContent = `${tasa.porcentaje}%`; // Solo el porcentaje
                option.dataset.porcentaje = tasa.porcentaje; // Guardar el porcentaje en un data attribute
                select.appendChild(option);
            });

            // Restaurar el valor seleccionado si aún es válido
            if (selectedValue) {
                select.value = selectedValue;
            }
        });
    }

    setupEventListeners() {
        // Permitir agregar productos SIN proveedor (validar solo al enviar)
        this.proveedorSelect.addEventListener('change', () => {
            this.validateForm();
        });

        // Quick supplier buttons
        document.querySelectorAll('.quick-supplier-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.proveedorSelect.value = btn.dataset.supplierId;
                this.proveedorSelect.dispatchEvent(new Event('change', { bubbles: true }));
                document.querySelectorAll('.quick-supplier-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        // Add row button - SIN validación de proveedor
        this.addRowBtn.addEventListener('click', () => {
            this.addFormRow();
        });

        // Delete row buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.delete-row-btn')) {
                e.preventDefault();
                const row = e.target.closest('tr.formset-row');
                if (row) this.deleteRow(row);
            }
        });

        // Copy row button (NEW)
        document.addEventListener('click', (e) => {
            if (e.target.closest('.copy-row-btn')) {
                e.preventDefault();
                const row = e.target.closest('tr.formset-row');
                if (row) this.copyRow(row);
            }
        });

        // Product selection with auto-fill
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('producto-select')) {
                this.handleProductSelection(e.target);
            }
        });

        // Live calculations
        document.addEventListener('input', (e) => {
            if (e.target.classList.contains('cantidad-input') || 
                e.target.classList.contains('costo-unitario-input')) {
                this.calculateTotals();
            }
        });

        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('iva-select')) {
                this.calculateTotals();
            }
        });

        // Form validation
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('producto-select') ||
                e.target.classList.contains('cantidad-input') ||
                e.target.classList.contains('costo-unitario-input') ||
                e.target.type === 'date') {
                this.validateField(e.target);
                this.validateForm();
            }
        });

        // Cancel button
        this.cancelarBtn.addEventListener('click', (e) => this.handleCancel(e));

        // Form submission
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    
    addFormRow() {
        const totalForms = parseInt(this.managementForm.value);
        const emptyForm = document.getElementById('empty-form-template').querySelector('tr');
        const newRow = emptyForm.cloneNode(true);
        
        newRow.classList.add('formset-row');
        newRow.id = `detalle-row-${totalForms}`;
        
        newRow.querySelectorAll('input, select').forEach(field => {
            const name = field.name;
            if (name) {
                field.name = name.replace(/__prefix__/g, totalForms);
                field.id = field.id ? field.id.replace(/__prefix__/g, totalForms) : '';
                field.value = '';
            }
        });

        newRow.style.opacity = '0';
        newRow.style.backgroundColor = '#fff3cd';
        this.detalleTable.querySelector('tbody').appendChild(newRow);

        setTimeout(() => {
            newRow.style.transition = 'opacity 0.3s ease, background-color 0.5s ease';
            newRow.style.opacity = '1';
            setTimeout(() => newRow.style.backgroundColor = '', 1000);
        }, 10);

        this.managementForm.value = totalForms + 1;
        newRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        const ivaSelect = newRow.querySelector('.iva-select');
        if (ivaSelect) {
            const tasas = this.tasasIva?.length > 0 ? this.tasasIva : [];
            tasas.forEach(tasa => {
                const option = document.createElement('option');
                option.value = tasa.id; // Usar el ID de la tasa como valor
                option.textContent = `${tasa.porcentaje}%`; // Solo el porcentaje
                option.dataset.porcentaje = tasa.porcentaje; // Guardar el porcentaje
                ivaSelect.appendChild(option);
            });
        }
        
        // Setup Tab navigation para la nueva fila
        this.setupRowTabNavigation(newRow);
        
        // Atajos de teclado para velocidad
        this.setupRowKeyboardShortcuts(newRow);
        
        const firstInput = newRow.querySelector('.producto-select');
        if (firstInput) setTimeout(() => firstInput.focus(), 300);

        this.calculateTotals();
        this.validateForm();
        this.updateProductCount();
    }

    setupRowTabNavigation(row) {
        const fields = row.querySelectorAll('.producto-select, .cantidad-input, .costo-unitario-input, .iva-select, [type="date"], .delete-row-btn, .copy-row-btn');
        
        fields.forEach((field, index) => {
            field.addEventListener('keydown', (e) => {
                if (e.key === 'Tab' && !e.shiftKey && index === fields.length - 1) {
                    e.preventDefault();
                    this.addFormRow();
                }
            });
        });
    }

    setupRowKeyboardShortcuts(row) {
        const cantidadInput = row.querySelector('.cantidad-input');
        const costoInput = row.querySelector('.costo-unitario-input');
        const deleteBtn = row.querySelector('.delete-row-btn');
        const copyBtn = row.querySelector('.copy-row-btn');

        // Ctrl+D: Duplicar fila
        row.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'd') {
                e.preventDefault();
                this.copyRow(row);
            }
        });

        // Ctrl+Backspace: Eliminar fila
        row.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Backspace') {
                e.preventDefault();
                this.deleteRow(row);
            }
        });

        // Ctrl+Enter en cantidad: Ir a costo
        if (cantidadInput) {
            cantidadInput.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 'Enter') {
                    e.preventDefault();
                    costoInput?.focus();
                }
            });
        }
    }

    deleteRow(row) {
        row.style.transition = 'opacity 0.3s ease';
        row.style.opacity = '0';
        setTimeout(() => {
            row.remove();
            this.updateProductCount();
            this.calculateTotals();
            this.validateForm();
        }, 300);
    }

    copyRow(sourceRow) {
        const totalForms = parseInt(this.managementForm.value);
        const newRow = sourceRow.cloneNode(true);
        
        newRow.id = `detalle-row-${totalForms}`;
        newRow.querySelectorAll('input, select').forEach(field => {
            const name = field.name;
            if (name) {
                field.name = name.replace(/\d+/g, totalForms);
                field.id = field.id ? field.id.replace(/\d+/g, totalForms) : '';
            }
        });

        newRow.style.opacity = '0';
        newRow.style.backgroundColor = '#d4edda';
        this.detalleTable.querySelector('tbody').appendChild(newRow);

        setTimeout(() => {
            newRow.style.transition = 'opacity 0.3s ease, background-color 0.5s ease';
            newRow.style.opacity = '1';
            setTimeout(() => newRow.style.backgroundColor = '', 1000);
        }, 10);

        this.managementForm.value = totalForms + 1;
        this.calculateTotals();
        this.validateForm();
        this.updateProductCount();
    }

    handleProductSelection(selectElement) {
        const productId = selectElement.value;
        const row = selectElement.closest('tr.formset-row');
        if (!row || !productId) return;

        const producto = this.productMap.get(parseInt(productId));
        if (!producto) return;

        // Auto-fill costo unitario
        const costoInput = row.querySelector('.costo-unitario-input');
        if (costoInput && producto.precio_unitario) {
            costoInput.value = producto.precio_unitario;
            costoInput.classList.add('is-valid');
            costoInput.classList.remove('is-invalid');
        }

        // Auto-fill IVA
        const ivaSelect = row.querySelector('.iva-select');
        const ivaId = producto.tasa_iva_id || '';
        
        if (ivaSelect) {
            ivaSelect.value = ivaId;
            ivaSelect.classList.add('is-valid');
        }

        // Sugerir cantidad basada en stock actual (si está disponible)
        const cantidadInput = row.querySelector('.cantidad-input');
        if (cantidadInput && producto.stock_actual !== undefined) {
            const suggestedQty = Math.max(10, Math.ceil(producto.stock_actual * 0.5));
            cantidadInput.placeholder = `Sugerido: ${suggestedQty}`;
            cantidadInput.setAttribute('data-suggested', suggestedQty);
            cantidadInput.setAttribute('title', `Stock actual: ${producto.stock_actual} | Sugerido: ${suggestedQty}`);
        }

        // Auto-focus cantidad para entrada rápida
        if (cantidadInput) {
            setTimeout(() => cantidadInput.focus(), 100);
        }

        this.calculateTotals();
        this.validateField(selectElement);
    }

    calculateTotals() {
        let grandSubtotal = 0;
        let grandIva = 0;

        this.detalleTable.querySelectorAll('tbody tr.formset-row').forEach(row => {
            const cantidadInput = row.querySelector('.cantidad-input');
            const costoInput = row.querySelector('.costo-unitario-input');
            const ivaSelect = row.querySelector('.iva-select');
            const subtotalDisplay = row.querySelector('.subtotal-display');

            if (cantidadInput && costoInput && ivaSelect) {
                const cantidad = parseFloat(cantidadInput.value) || 0;
                const costo = parseFloat(costoInput.value) || 0;

                const selectedOption = ivaSelect.options[ivaSelect.selectedIndex];
                const ivaPorcentaje = selectedOption ? parseFloat(selectedOption.dataset.porcentaje) || 0 : 0;

                const subtotal = cantidad * costo;
                const iva = subtotal * (ivaPorcentaje / 100);
                const total = subtotal + iva;

                // Update hidden IVA field for form submission
                const ivaField = row.querySelector('.iva-field');
                if (ivaField) {
                    ivaField.value = iva.toFixed(2);
                }

                grandSubtotal += subtotal;
                grandIva += iva;

                if (subtotalDisplay) {
                    subtotalDisplay.textContent = this.formatCurrency(total);
                }
            }
        });

        const grandTotal = grandSubtotal + grandIva;
        document.getElementById('gran-subtotal').textContent = this.formatCurrency(grandSubtotal);
        document.getElementById('gran-iva').textContent = this.formatCurrency(grandIva);
        document.getElementById('gran-total').textContent = this.formatCurrency(grandTotal);
    }

    formatCurrency(value) {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    }

    validateField(field) {
        const row = field.closest('tr.formset-row');
        if (!row) return true;

        let isValid = true;
        let errorMsg = '';
        let errorType = '';

        if (field.classList.contains('producto-select')) {
            isValid = !!field.value;
            if (isValid) {
                errorType = 'success';
            } else {
                errorMsg = 'Selecciona un producto';
                errorType = 'error';
            }
        } else if (field.classList.contains('cantidad-input')) {
            const value = parseFloat(field.value);
            if (!field.value) {
                isValid = false;
                errorMsg = 'Cantidad requerida';
                errorType = 'error';
            } else if (value <= 0) {
                isValid = false;
                errorMsg = 'Cantidad debe ser > 0';
                errorType = 'error';
            } else if (value > 999999) {
                isValid = false;
                errorMsg = 'Cantidad muy alta';
                errorType = 'warning';
            } else {
                errorType = 'success';
            }
        } else if (field.classList.contains('costo-unitario-input')) {
            const value = parseFloat(field.value);
            if (!field.value) {
                isValid = false;
                errorMsg = 'Costo requerido';
                errorType = 'error';
            } else if (value <= 0) {
                isValid = false;
                errorMsg = 'Costo debe ser > 0';
                errorType = 'error';
            } else if (value > 999999999) {
                isValid = false;
                errorMsg = 'Costo muy alto';
                errorType = 'warning';
            } else {
                errorType = 'success';
            }
        } else if (field.type === 'date') {
            const today = new Date().toISOString().split('T')[0];
            if (!field.value) {
                isValid = false;
                errorMsg = 'Fecha requerida';
                errorType = 'error';
            } else if (field.value < today) {
                isValid = false;
                errorMsg = 'Fecha no puede ser pasada';
                errorType = 'error';
            } else {
                errorType = 'success';
            }
        }

        field.classList.toggle('is-invalid', !isValid);
        field.classList.toggle('is-valid', isValid && errorType === 'success');
        field.classList.toggle('is-warning', errorType === 'warning');
        
        // Mostrar feedback visual en vivo con tooltip
        if (errorMsg) {
            field.setAttribute('data-error', errorMsg);
            field.setAttribute('title', errorMsg);
            // Agregar pequeño indicador visual debajo del campo
            this.showFieldError(field, errorMsg, errorType);
        } else {
            field.removeAttribute('data-error');
            field.removeAttribute('title');
            this.clearFieldError(field);
        }

        return isValid;
    }

    showFieldError(field, message, type) {
        let errorEl = field.nextElementSibling;
        if (!errorEl || !errorEl.classList.contains('field-error-msg')) {
            errorEl = document.createElement('small');
            errorEl.className = 'field-error-msg d-block mt-1';
            field.parentNode.insertBefore(errorEl, field.nextSibling);
        }
        errorEl.textContent = message;
        errorEl.className = `field-error-msg d-block mt-1 text-${type === 'error' ? 'danger' : 'warning'}`;
    }

    clearFieldError(field) {
        const errorEl = field.nextElementSibling;
        if (errorEl && errorEl.classList.contains('field-error-msg')) {
            errorEl.remove();
        }
    }

    validateForm() {
        let isValid = true;
        let validCount = 0;
        let totalChecks = 0;

        // Validar proveedor (requerido)
        if (!this.proveedorSelect || !this.proveedorSelect.value) {
            isValid = false;
            this.proveedorSelect?.classList.add('is-invalid');
        } else {
            this.proveedorSelect?.classList.remove('is-invalid');
            validCount++;
        }
        totalChecks++;

        const rows = this.detalleTable.querySelectorAll('tbody tr.formset-row');
        if (rows.length === 0) {
            isValid = false;
        } else {
            validCount += rows.length;
        }
        totalChecks += rows.length;

        let errorCount = 0;
        rows.forEach(row => {
            const producto = row.querySelector('.producto-select');
            const cantidad = row.querySelector('.cantidad-input');
            const costo = row.querySelector('.costo-unitario-input');
            const fecha = row.querySelector('[type="date"]');

            let rowValid = true;
            [producto, cantidad, costo, fecha].forEach(field => {
                if (field && !this.validateField(field)) {
                    rowValid = false;
                    isValid = false;
                    errorCount++;
                }
            });

            row.classList.toggle('row-error', !rowValid);
            row.classList.toggle('row-valid', rowValid);
        });

        // Actualizar barra de validación
        const percentage = totalChecks > 0 ? Math.round(((totalChecks - errorCount) / totalChecks) * 100) : 0;
        const validationBar = document.getElementById('formValidationBar');
        if (validationBar) {
            validationBar.style.width = `${percentage}%`;
            validationBar.setAttribute('aria-valuenow', percentage);
            validationBar.className = `progress-bar ${percentage === 100 ? 'bg-success' : percentage > 50 ? 'bg-info' : 'bg-warning'}`;
        }

        this.guardarBtn.disabled = !isValid;
        return isValid;
    }

    updateProductCount() {
        const rows = this.detalleTable.querySelectorAll('tbody tr.formset-row');
        this.managementForm.value = rows.length;
        document.getElementById('product-count').textContent = rows.length;
    }

    updateAddRowButton() {
        const hasSupplier = !!this.proveedorSelect.value;
        this.addRowBtn.disabled = !hasSupplier;
        this.addRowBtn.title = hasSupplier ? 'Agregar producto (Tab al final)' : 'Selecciona un proveedor primero';
    }

    handleCancel(e) {
        e.preventDefault();
        const hasData = this.detalleTable.querySelectorAll('tbody tr.formset-row').length > 0 ||
                       (this.proveedorSelect && this.proveedorSelect.value);

        if (hasData && typeof Swal !== 'undefined') {
            Swal.fire({
                title: '¿Cancelar?',
                text: 'Se perderán todos los cambios.',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#dc3545',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'Sí, cancelar',
                cancelButtonText: 'Volver'
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = cancelUrl;
                }
            });
        } else {
            window.location.href = cancelUrl;
        }
    }

    handleSubmit(e) {
        if (!this.validateForm()) {
            e.preventDefault();
            e.stopPropagation();
            
            // Encontrar primer error
            const firstError = this.form.querySelector('.is-invalid');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                setTimeout(() => firstError.focus(), 300);
                this.showToast('Corrige los errores marcados en rojo', 'danger');
            }
        } else {
            this.guardarBtn.disabled = true;
            this.guardarBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Guardando...';
        }
    }

    showToast(message, type = 'info') {
        const toastContainer = document.querySelector('.toast-container') || this.createToastContainer();
        const toastId = `toast-${Date.now()}`;
        
        const icons = {
            'success': 'fa-check-circle',
            'danger': 'fa-exclamation-circle',
            'warning': 'fa-exclamation-triangle',
            'info': 'fa-info-circle'
        };
        
        const toastHTML = `
            <div id="${toastId}" class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header bg-${type} text-white">
                    <i class="fas ${icons[type]} me-2"></i>
                    <strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        const toastElement = document.getElementById(toastId);
        
        if (type !== 'danger') {
            setTimeout(() => {
                toastElement.classList.remove('show');
                setTimeout(() => toastElement.remove(), 300);
            }, 4000);
        }
    }

    createToastContainer() {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        return container;
    }
}

// ============================================
// SMART PRODUCT SEARCH (AUTOCOMPLETADO)
// ============================================
class SmartProductSearch {
    constructor(productos) {
        this.productos = productos;
        this.setupSearchListeners();
    }

    setupSearchListeners() {
        document.addEventListener('focus', (e) => {
            if (e.target.classList.contains('producto-select')) {
                this.initializeSelect2(e.target);
            }
        }, true);
    }

    initializeSelect2(selectElement) {
        if (selectElement.dataset.select2Initialized) return;

        $(selectElement).select2({
            placeholder: 'Buscar producto...',
            allowClear: true,
            width: '100%',
            data: this.productos.map(p => ({
                id: p.id,
                text: `${p.nombre} (${p.precio_unitario ? '$' + p.precio_unitario : 'N/A'})`
            })),
            matcher: (params, data) => {
                if (!params.term) return data;
                const term = params.term.toLowerCase();
                if (data.text.toLowerCase().includes(term)) return data;
                return null;
            }
        });

        selectElement.dataset.select2Initialized = true;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const form = new ReabastecimientoForm();
    new SmartProductSearch(form.productos);
});
