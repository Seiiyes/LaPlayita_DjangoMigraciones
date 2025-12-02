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
        // Disable HTML5 validation to prevent "not focusable" errors
        this.form.setAttribute('novalidate', 'novalidate');
        
        this.initializeProveedorSelect();
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
    
    initializeProveedorSelect() {
        // NO usar Select2 para el proveedor, solo deshabilitar autocompletado nativo
        if (this.proveedorSelect) {
            this.proveedorSelect.setAttribute('autocomplete', 'off');
            this.proveedorSelect.setAttribute('autocomplete', 'new-password'); // Truco para deshabilitar autocompletado
        }
    }
    
    populateIvaSelects() {
        document.querySelectorAll('.iva-select').forEach(select => {
            // Solo poblar si el select solo tiene el placeholder (1 opción)
            if (select.options.length > 1) return;
            
            // Guardar el valor seleccionado si existe
            const selectedValue = select.value;
            
            // Usar this.tasasIva que viene del contexto de Django
            const tasas = this.tasasIva?.length > 0 ? this.tasasIva : [];
            
            tasas.forEach(tasa => {
                const option = document.createElement('option');
                option.value = tasa.id; // Usar el ID de la tasa como valor
                option.textContent = tasa.nombre; // Solo el nombre (ya incluye el porcentaje)
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
                this.updateProductCount(); // Actualizar contador al seleccionar producto
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
        
        // Guardar como borrador button
        const guardarBorradorBtn = document.getElementById('guardarBorradorBtn');
        if (guardarBorradorBtn) {
            guardarBorradorBtn.addEventListener('click', (e) => this.handleSaveDraft(e));
        }

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
        
        // Poblar el select de IVA de la nueva fila
        this.populateIvaSelects();
        
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
        
        // Actualizar vista móvil
        this.syncMobileView();
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
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const selectedDate = field.value ? new Date(field.value + 'T00:00:00') : null;
            
            if (!field.value) {
                isValid = false;
                errorMsg = 'Fecha requerida';
                errorType = 'error';
            } else if (selectedDate < today) {
                isValid = false;
                errorMsg = 'Fecha no puede ser pasada';
                errorType = 'error';
            } else {
                // Advertencia si la fecha es muy cercana (menos de 7 días)
                const diffDays = Math.ceil((selectedDate - today) / (1000 * 60 * 60 * 24));
                if (diffDays < 7) {
                    errorMsg = `Caducidad cercana (${diffDays} días)`;
                    errorType = 'warning';
                } else {
                    errorType = 'success';
                }
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
        // Primero limpiar cualquier error existente
        this.clearFieldError(field);
        
        // Crear nuevo elemento de error
        const errorEl = document.createElement('small');
        errorEl.className = `field-error-msg d-block mt-1 text-${type === 'error' ? 'danger' : 'warning'}`;
        errorEl.textContent = message;
        
        // Insertar después del campo
        field.parentNode.insertBefore(errorEl, field.nextSibling);
    }

    clearFieldError(field) {
        // Buscar y eliminar TODOS los mensajes de error después del campo
        let nextEl = field.nextElementSibling;
        while (nextEl && nextEl.classList.contains('field-error-msg')) {
            const toRemove = nextEl;
            nextEl = nextEl.nextElementSibling;
            toRemove.remove();
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
        
        // Filtrar solo las filas que tienen un producto seleccionado
        const rowsWithProduct = Array.from(rows).filter(row => {
            const producto = row.querySelector('.producto-select');
            return producto && producto.value && producto.value !== '';
        });

        if (rowsWithProduct.length === 0) {
            isValid = false;
        } else {
            validCount += rowsWithProduct.length;
        }
        totalChecks += rowsWithProduct.length;

        let errorCount = 0;
        
        // Solo validar filas con producto seleccionado
        rowsWithProduct.forEach(row => {
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

        // Limpiar validación de filas vacías (sin producto)
        rows.forEach(row => {
            const producto = row.querySelector('.producto-select');
            if (!producto || !producto.value || producto.value === '') {
                // Limpiar clases de validación
                row.classList.remove('row-error', 'row-valid');
                
                // Limpiar validación de todos los campos de la fila
                const fields = row.querySelectorAll('.producto-select, .cantidad-input, .costo-unitario-input, [type="date"]');
                fields.forEach(field => {
                    field.classList.remove('is-invalid', 'is-valid');
                    this.clearFieldError(field);
                });
            }
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
        // Solo contar filas visibles en el tbody principal (no el template oculto)
        const tbody = this.detalleTable.querySelector('tbody');
        const rows = tbody ? tbody.querySelectorAll('tr.formset-row') : [];
        this.managementForm.value = rows.length;
        
        // Contar solo filas con producto seleccionado (no filas vacías)
        let count = 0;
        rows.forEach(row => {
            const productoSelect = row.querySelector('.producto-select');
            if (productoSelect) {
                const value = productoSelect.value;
                const selectedIndex = productoSelect.selectedIndex;
                
                // Verificar que tenga un valor válido (no vacío y no el placeholder)
                if (value && value !== '' && selectedIndex > 0) {
                    count++;
                }
            }
        });
        
        const countElement = document.getElementById('product-count');
        if (countElement) {
            countElement.textContent = count;
        }
        this.syncMobileView();
    }
    
    syncMobileView() {
        // Sincronizar vista móvil con la tabla
        const mobileView = document.getElementById('mobileCardView');
        if (!mobileView) return;
        
        const rows = this.detalleTable.querySelectorAll('tbody tr.formset-row');
        let html = '';
        
        rows.forEach((row, index) => {
            const productoSelect = row.querySelector('.producto-select');
            const cantidadInput = row.querySelector('.cantidad-input');
            const costoInput = row.querySelector('.costo-unitario-input');
            const ivaSelect = row.querySelector('.iva-select');
            const fechaInput = row.querySelector('[type="date"]');
            const subtotalDisplay = row.querySelector('.subtotal-display');
            
            const productoNombre = productoSelect.options[productoSelect.selectedIndex]?.text || 'Seleccionar producto';
            const cantidad = cantidadInput.value || '0';
            const costo = costoInput.value || '0';
            const iva = ivaSelect.options[ivaSelect.selectedIndex]?.text || '--';
            const fecha = fechaInput.value || '';
            const subtotal = subtotalDisplay.textContent || '$0';
            
            html += `
                <div class="mobile-product-card" data-row-index="${index}">
                    <div class="card-header">
                        <strong>Producto ${index + 1}</strong>
                        <button type="button" class="btn btn-sm btn-outline-danger mobile-delete-btn" data-row-index="${index}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                    <div class="form-group">
                        <label>Producto</label>
                        <div class="text-muted">${productoNombre}</div>
                    </div>
                    <div class="row">
                        <div class="col-6 form-group">
                            <label>Cantidad</label>
                            <div class="fw-bold">${cantidad}</div>
                        </div>
                        <div class="col-6 form-group">
                            <label>Costo Unit.</label>
                            <div class="fw-bold">$${parseFloat(costo || 0).toLocaleString('es-CO')}</div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-6 form-group">
                            <label>IVA</label>
                            <div>${iva}</div>
                        </div>
                        <div class="col-6 form-group">
                            <label>Caducidad</label>
                            <div>${fecha || 'No especificada'}</div>
                        </div>
                    </div>
                    <div class="subtotal-badge">
                        Total: ${subtotal}
                    </div>
                </div>
            `;
        });
        
        if (rows.length === 0) {
            html = '<div class="text-center text-muted py-4">No hay productos agregados</div>';
        }
        
        mobileView.innerHTML = html;
        
        // Agregar event listeners para botones de eliminar en móvil
        mobileView.querySelectorAll('.mobile-delete-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const rowIndex = parseInt(btn.dataset.rowIndex);
                const tableRow = this.detalleTable.querySelectorAll('tbody tr.formset-row')[rowIndex];
                if (tableRow) this.deleteRow(tableRow);
            });
        });
    }

    updateAddRowButton() {
        const hasSupplier = !!this.proveedorSelect.value;
        this.addRowBtn.disabled = !hasSupplier;
        this.addRowBtn.title = hasSupplier ? 'Agregar producto (Tab al final)' : 'Selecciona un proveedor primero';
    }

    handleSaveDraft(e) {
        e.preventDefault();
        console.log('[BORRADOR] Iniciando guardado de borrador...');
        
        // Validar que al menos haya un proveedor
        if (!this.proveedorSelect.value) {
            console.log('[BORRADOR] Error: No hay proveedor seleccionado');
            Swal.fire({
                icon: 'warning',
                title: 'Proveedor requerido',
                text: 'Debes seleccionar un proveedor para guardar el borrador.',
                confirmButtonColor: '#0d6efd'
            });
            return;
        }
        
        const rows = this.detalleTable.querySelectorAll('tbody:not(#empty-form-template) tr.formset-row');
        console.log(`[BORRADOR] Filas encontradas: ${rows.length}`);
        
        // Cambiar el estado a borrador
        const estadoInput = this.form.querySelector('[name="estado"]');
        if (estadoInput) {
            estadoInput.value = 'borrador';
            console.log('[BORRADOR] Estado cambiado a: borrador');
        } else {
            console.error('[BORRADOR] No se encontró el campo de estado');
        }
        
        const guardarBtn = document.getElementById('guardarBorradorBtn');
        if (guardarBtn) {
            guardarBtn.disabled = true;
            guardarBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Guardando...';
        }
        
        console.log('[BORRADOR] Enviando formulario...');
        this.form.submit();
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
            // Mostrar confirmación antes de guardar
            e.preventDefault();
            const rows = this.detalleTable.querySelectorAll('tbody tr.formset-row');
            const productCount = rows.length;
            const total = document.getElementById('gran-total').textContent;
            
            // Enviar directamente sin confirmación adicional para mayor velocidad
            this.guardarBtn.disabled = true;
            this.guardarBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Enviando...';
            this.form.submit();
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
        // Ya no usamos Select2, solo select nativo
        // Los selects nativos funcionan mejor para este caso
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const form = new ReabastecimientoForm();
    new SmartProductSearch(form.productos);
    
    // Exponer función global para importación desde Excel
    window.addProductosFromExcel = function(productos) {
        console.log('[EXCEL IMPORT] Agregando productos al formulario:', productos);
        
        // Limpiar TODAS las filas existentes antes de importar
        const tbody = form.detalleTable.querySelector('tbody');
        const existingRows = tbody.querySelectorAll('tr.formset-row');
        console.log('[EXCEL IMPORT] Limpiando todas las filas existentes:', existingRows.length);
        existingRows.forEach(row => {
            row.remove();
        });
        
        // Resetear el contador de formularios a 0
        form.managementForm.value = 0;
        console.log('[EXCEL IMPORT] Contador de formularios reseteado a 0');
        
        // Guardar referencia al template ANTES de empezar a clonar
        const template = document.getElementById('empty-form-template');
        if (!template) {
            console.error('[EXCEL IMPORT] No se encontró el template');
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'No se pudo encontrar el template del formulario',
                confirmButtonColor: '#dc3545'
            });
            return;
        }
        
        // Verificar que tenemos el tbody correcto de la tabla principal
        const mainTbody = form.detalleTable.querySelector('tbody');
        console.log('[EXCEL IMPORT] Tbody principal encontrado:', !!mainTbody);
        console.log('[EXCEL IMPORT] ID de la tabla:', form.detalleTable.id);
        
        const templateRow = template.querySelector('tr');
        if (!templateRow) {
            console.error('[EXCEL IMPORT] No se encontró el <tr> en el template');
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'El template del formulario está corrupto',
                confirmButtonColor: '#dc3545'
            });
            return;
        }
        
        // Guardar una copia del template para poder clonar múltiples veces
        const templateClone = templateRow.cloneNode(true);
        
        // Función para llenar una fila con datos
        const fillRow = (rowIndex, producto) => {
            return new Promise((resolve) => {
                console.log(`[EXCEL IMPORT] Procesando producto ${rowIndex + 1}:`, producto);
                
                // Clonar desde la copia guardada
                const newRow = templateClone.cloneNode(true);
                const totalForms = parseInt(form.managementForm.value);
                
                // Asegurar que la fila sea visible desde el inicio
                newRow.style.display = 'table-row';
                newRow.classList.remove('d-none');
                newRow.classList.add('formset-row');
                
                // Actualizar nombres e IDs
                newRow.querySelectorAll('input, select').forEach(field => {
                    const name = field.name;
                    if (name) {
                        field.name = name.replace(/__prefix__/g, totalForms);
                        field.id = field.id ? field.id.replace(/__prefix__/g, totalForms) : '';
                    }
                });
                
                // Agregar al DOM - Asegurarse de usar el tbody correcto (no el del template)
                const allTbodies = document.querySelectorAll('tbody');
                console.log(`[EXCEL IMPORT] Total de tbody encontrados: ${allTbodies.length}`);
                
                // El primer tbody es el de la tabla principal, el segundo es el del template oculto
                const tbody = form.detalleTable.querySelector('tbody:not(#empty-form-template)');
                if (!tbody) {
                    console.error('[EXCEL IMPORT] No se encontró el tbody de la tabla principal');
                    resolve();
                    return;
                }
                
                console.log(`[EXCEL IMPORT] Usando tbody:`, tbody.parentElement.id);
                tbody.appendChild(newRow);
                const newTotalForms = totalForms + 1;
                form.managementForm.value = newTotalForms;
                
                console.log(`[EXCEL IMPORT] Fila ${rowIndex + 1} creada y agregada al DOM`);
                console.log(`[EXCEL IMPORT] TOTAL_FORMS actualizado a: ${newTotalForms}`);
                console.log(`[EXCEL IMPORT] Fila visible:`, newRow.style.display, newRow.classList.contains('formset-row'));
                console.log(`[EXCEL IMPORT] Total filas en tbody principal:`, tbody.querySelectorAll('tr').length);
                
                // Verificar los nombres de los campos
                const productoField = newRow.querySelector('select[name*="producto"]');
                const cantidadField = newRow.querySelector('input[name*="cantidad"]');
                console.log(`[EXCEL IMPORT] Nombres de campos - Producto: ${productoField?.name}, Cantidad: ${cantidadField?.name}`);
                
                // Esperar un momento para que se renderice
                setTimeout(() => {
                    // Buscar campos en la nueva fila
                    const productoSelect = newRow.querySelector('select[name*="producto"]');
                    const cantidadInput = newRow.querySelector('input[name*="cantidad"]');
                    const costoInput = newRow.querySelector('input[name*="costo_unitario"]');
                    const ivaSelect = newRow.querySelector('select.iva-select');
                    const fechaInput = newRow.querySelector('input[name*="fecha_caducidad"]');
                    
                    console.log(`[EXCEL IMPORT] Campos encontrados:`, {
                        producto: !!productoSelect,
                        cantidad: !!cantidadInput,
                        costo: !!costoInput,
                        iva: !!ivaSelect,
                        fecha: !!fechaInput
                    });
                    
                    // Llenar producto - primero poblar opciones
                    if (productoSelect) {
                        // Limpiar opciones existentes
                        productoSelect.innerHTML = '<option value="">Seleccionar producto...</option>';
                        
                        // Agregar todas las opciones de productos
                        form.productos.forEach(p => {
                            const option = document.createElement('option');
                            option.value = p.id;
                            option.textContent = p.nombre;
                            productoSelect.appendChild(option);
                        });
                        
                        // Ahora seleccionar el producto
                        productoSelect.value = producto.producto_id;
                        console.log(`[EXCEL IMPORT] Producto seleccionado: ${producto.producto_id} (${producto.producto_nombre})`);
                        productoSelect.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                    
                    // Llenar cantidad
                    if (cantidadInput) {
                        cantidadInput.value = producto.cantidad;
                        console.log(`[EXCEL IMPORT] Cantidad: ${producto.cantidad}`);
                        cantidadInput.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                    
                    // Llenar costo
                    if (costoInput) {
                        costoInput.value = producto.costo_unitario;
                        console.log(`[EXCEL IMPORT] Costo: ${producto.costo_unitario}`);
                        costoInput.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                    
                    // Poblar y seleccionar IVA
                    if (ivaSelect) {
                        // Poblar opciones de IVA
                        form.populateIvaSelects();
                        
                        if (producto.tasa_iva_id) {
                            setTimeout(() => {
                                ivaSelect.value = producto.tasa_iva_id;
                                console.log(`[EXCEL IMPORT] IVA: ${producto.tasa_iva_id}`);
                                ivaSelect.dispatchEvent(new Event('change', { bubbles: true }));
                            }, 100);
                        }
                    }
                    
                    // Llenar fecha
                    if (fechaInput && producto.fecha_caducidad) {
                        fechaInput.value = producto.fecha_caducidad;
                        console.log(`[EXCEL IMPORT] Fecha: ${producto.fecha_caducidad}`);
                    }
                    
                    console.log(`[EXCEL IMPORT] Producto ${rowIndex + 1} completado`);
                    
                    // Forzar actualización visual y asegurar visibilidad
                    newRow.style.display = 'table-row';
                    newRow.style.visibility = 'visible';
                    newRow.classList.add('formset-row');
                    newRow.classList.remove('d-none');
                    
                    // Hacer scroll a la fila si es necesario
                    if (rowIndex === 0) {
                        newRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                    
                    // Esperar antes de resolver
                    setTimeout(() => {
                        resolve();
                    }, 200);
                }, 300);
            });
        };
        
        // Procesar productos secuencialmente
        const processProductos = async () => {
            for (let i = 0; i < productos.length; i++) {
                await fillRow(i, productos[i]);
            }
            
            // Actualizar totales al final
            setTimeout(() => {
                console.log('[EXCEL IMPORT] Actualizando totales y validación...');
                
                // Forzar recálculo de totales
                form.calculateTotals();
                form.updateProductCount();
                form.validateForm();
                
                // Poblar todos los selects de IVA
                form.populateIvaSelects();
                
                // Verificar que las filas sean visibles
                const rows = document.querySelectorAll('tr.formset-row');
                console.log(`[EXCEL IMPORT] Total de filas en el DOM: ${rows.length}`);
                
                rows.forEach((row, idx) => {
                    const productoSelect = row.querySelector('select[name*="producto"]');
                    const cantidadInput = row.querySelector('input[name*="cantidad"]');
                    console.log(`[EXCEL IMPORT] Fila ${idx}: Producto=${productoSelect?.value}, Cantidad=${cantidadInput?.value}`);
                    
                    // Asegurar visibilidad completa
                    row.style.display = 'table-row';
                    row.style.visibility = 'visible';
                    row.classList.add('formset-row');
                    row.classList.remove('d-none');
                });
                
                // Hacer scroll a la tabla de productos
                const productosSection = document.querySelector('.reab-section');
                if (productosSection) {
                    productosSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
                
                // Verificar el estado final del formset
                const finalTotalForms = form.managementForm.value;
                console.log(`[EXCEL IMPORT] ✓ Todos los productos agregados exitosamente`);
                console.log(`[EXCEL IMPORT] Estado final - TOTAL_FORMS: ${finalTotalForms}`);
                
                // Listar todos los campos del formset
                for (let i = 0; i < finalTotalForms; i++) {
                    const productoField = document.querySelector(`[name="reabastecimientodetalle_set-${i}-producto"]`);
                    const cantidadField = document.querySelector(`[name="reabastecimientodetalle_set-${i}-cantidad"]`);
                    console.log(`[EXCEL IMPORT] Formset ${i}: producto=${productoField?.value}, cantidad=${cantidadField?.value}`);
                }
            }, 500);
        };
        
        processProductos();
    };
});
