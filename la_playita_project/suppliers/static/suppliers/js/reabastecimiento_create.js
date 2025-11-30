// Reabastecimiento Create Form Handler
// Updated: 2025-11-29 - Fixed cancel button URL

// Proteger contra modales faltantes
document.addEventListener('show.bs.modal', function(e) {
    if (!e.target) {
        e.preventDefault();
    }
}, true);

document.addEventListener('DOMContentLoaded', function() {
    const addRowBtn = document.getElementById('add-row-formset');
    const emptyFormTemplate = document.getElementById('empty-form-template');
    const detalleTable = document.getElementById('detalleTable');
    const managementForm = document.querySelector('[name="reabastecimientodetalle_set-TOTAL_FORMS"]');
    const proveedorSelect = document.getElementById('id_proveedor_select');
    const proveedorDisplay = document.getElementById('proveedor-display');
    
    // Actualizar proveedor en header sticky
    if (proveedorSelect) {
        proveedorSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            proveedorDisplay.textContent = selectedOption.text || 'Seleccionar...';
        });
    }
    
    // Add row button
    if (addRowBtn) {
        addRowBtn.addEventListener('click', function() {
            addFormRow();
        });
    }
    
    // Delete row buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.delete-row-btn')) {
            e.preventDefault();
            const row = e.target.closest('tr.formset-row');
            if (row) {
                // Animar salida
                row.style.transition = 'opacity 0.3s ease';
                row.style.opacity = '0';
                
                setTimeout(() => {
                    row.remove();
                    updateFormCount();
                    calculateTotals();
                    validateForm();
                }, 300);
            }
        }
    });
    
    // Calculate totals on input change
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('cantidad-input') || 
            e.target.classList.contains('costo-unitario-input') ||
            e.target.classList.contains('iva-porcentaje-input')) {
            calculateTotals();
        }
        
        // Handle product selection to fill price
        if (e.target.classList.contains('producto-select')) {
            handleProductSelection(e.target);
        }
    });
    
    // También calcular en input (para cambios en tiempo real)
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('cantidad-input') || 
            e.target.classList.contains('costo-unitario-input')) {
            calculateTotals();
        }
    });
    
    function handleProductSelection(selectElement) {
        const productId = selectElement.value;
        
        if (!productId) return;
        
        // Get the row containing this select
        const row = selectElement.closest('tr.formset-row');
        if (!row) return;
        
        // Find the costo_unitario input in this row
        const costoInput = row.querySelector('.costo-unitario-input');
        if (!costoInput) return;
        
        // Try to get price from productos array (if available globally)
        if (typeof productos !== 'undefined' && Array.isArray(productos)) {
            const producto = productos.find(p => p.id == productId);
            if (producto && producto.precio_unitario) {
                costoInput.value = producto.precio_unitario;
                costoInput.classList.add('is-valid');
                costoInput.classList.remove('is-invalid');
                
                // Mostrar feedback visual
                const feedback = document.createElement('small');
                feedback.className = 'text-success d-block mt-1';
                feedback.innerHTML = '<i class="fas fa-check-circle me-1"></i>Precio cargado';
                
                // Remover feedback anterior si existe
                const oldFeedback = row.querySelector('.price-feedback');
                if (oldFeedback) oldFeedback.remove();
                
                feedback.className += ' price-feedback';
                costoInput.parentElement.appendChild(feedback);
                
                // Remover feedback después de 2 segundos
                setTimeout(() => {
                    feedback.style.opacity = '0';
                    feedback.style.transition = 'opacity 0.3s ease';
                    setTimeout(() => feedback.remove(), 300);
                }, 2000);
                
                calculateTotals();
                return;
            }
        }
        
        // Try to get price from data attribute if available
        const selectedOption = selectElement.options[selectElement.selectedIndex];
        const precio = selectedOption.dataset.precio;
        if (precio) {
            costoInput.value = precio;
            costoInput.classList.add('is-valid');
            calculateTotals();
        }
    }
    
    function addFormRow() {
        const totalForms = parseInt(managementForm.value);
        const newRow = emptyFormTemplate.querySelector('tr').cloneNode(true);
        
        // Update form names
        newRow.querySelectorAll('input, select, textarea').forEach(field => {
            const name = field.name;
            if (name) {
                field.name = name.replace(/__prefix__/g, totalForms);
                field.id = field.id ? field.id.replace(/__prefix__/g, totalForms) : '';
            }
        });
        
        // Agregar animación
        newRow.style.opacity = '0';
        newRow.style.backgroundColor = '#fff3cd';
        detalleTable.querySelector('tbody').appendChild(newRow);
        
        // Animar entrada
        setTimeout(() => {
            newRow.style.transition = 'opacity 0.3s ease, background-color 0.5s ease';
            newRow.style.opacity = '1';
            
            // Remover highlight después de 1 segundo
            setTimeout(() => {
                newRow.style.backgroundColor = '';
            }, 1000);
        }, 10);
        
        managementForm.value = totalForms + 1;
        
        // Scroll a la nueva fila
        newRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // Focus en el primer input
        const firstInput = newRow.querySelector('input, select');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 300);
        }
        
        calculateTotals();
        validateForm();
        updateFormCount();
    }
    
    function updateFormCount() {
        const rows = detalleTable.querySelectorAll('tbody tr.formset-row');
        managementForm.value = rows.length;
        
        // Actualizar contador visual
        const productCount = document.getElementById('product-count');
        if (productCount) {
            productCount.textContent = rows.length;
            
            // Cambiar color según cantidad
            if (rows.length === 0) {
                productCount.className = 'text-danger';
            } else if (rows.length < 3) {
                productCount.className = 'text-warning';
            } else {
                productCount.className = 'text-success';
            }
        }
    }
    
    function calculateTotals() {
        let grandSubtotal = 0;
        let grandIva = 0;
        
        detalleTable.querySelectorAll('tbody tr.formset-row').forEach(row => {
            const cantidadInput = row.querySelector('.cantidad-input');
            const costoInput = row.querySelector('.costo-unitario-input');
            const ivaSelect = row.querySelector('.iva-porcentaje-input');
            
            if (cantidadInput && costoInput && ivaSelect) {
                const cantidad = parseFloat(cantidadInput.value) || 0;
                const costo = parseFloat(costoInput.value) || 0;
                const ivaPorcentaje = parseFloat(ivaSelect.value) || 0;
                
                const subtotal = cantidad * costo;
                const iva = subtotal * (ivaPorcentaje / 100);
                
                grandSubtotal += subtotal;
                grandIva += iva;
            }
        });
        
        const grandTotal = grandSubtotal + grandIva;
        
        // Formatear como moneda
        const formatter = new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
        
        document.getElementById('gran-subtotal').textContent = formatter.format(grandSubtotal);
        document.getElementById('gran-iva').textContent = formatter.format(grandIva);
        document.getElementById('gran-total').textContent = formatter.format(grandTotal);
        document.getElementById('total-display').textContent = formatter.format(grandTotal);
    }
    
    // Validación de campos requeridos en vivo
    const form = document.getElementById('reabastecimientoForm');
    const guardarBtn = document.getElementById('guardarReabastecimientoBtn');
    
    function validateField(field) {
        const row = field.closest('tr.formset-row');
        if (!row) return true;
        
        const fieldType = field.classList[0];
        let isValid = true;
        let errorMsg = '';
        let warningMsg = '';
        
        if (fieldType === 'producto-select') {
            if (!field.value) {
                isValid = false;
                errorMsg = '<i class="fas fa-exclamation-circle me-1"></i>Selecciona un producto';
            }
        } else if (fieldType === 'cantidad-input') {
            const value = parseFloat(field.value);
            if (!field.value || value <= 0) {
                isValid = false;
                errorMsg = '<i class="fas fa-exclamation-circle me-1"></i>Cantidad debe ser > 0';
            } else if (value > 999999) {
                isValid = false;
                errorMsg = '<i class="fas fa-exclamation-circle me-1"></i>Cantidad muy grande';
            } else if (value > 1000) {
                warningMsg = '<i class="fas fa-info-circle me-1"></i>Cantidad alta, verifica';
            }
        } else if (fieldType === 'costo-unitario-input') {
            const value = parseFloat(field.value);
            if (!field.value || value <= 0) {
                isValid = false;
                errorMsg = '<i class="fas fa-exclamation-circle me-1"></i>Costo debe ser > 0';
            } else if (value > 999999999) {
                isValid = false;
                errorMsg = '<i class="fas fa-exclamation-circle me-1"></i>Costo muy grande';
            }
        } else if (field.type === 'date') {
            const today = new Date().toISOString().split('T')[0];
            if (!field.value) {
                isValid = false;
                errorMsg = '<i class="fas fa-exclamation-circle me-1"></i>Fecha requerida';
            } else if (field.value < today) {
                isValid = false;
                errorMsg = '<i class="fas fa-exclamation-circle me-1"></i>Fecha no puede ser pasada';
            } else {
                const expiryDate = new Date(field.value);
                const maxDate = new Date();
                maxDate.setFullYear(maxDate.getFullYear() + 5);
                if (expiryDate > maxDate) {
                    isValid = false;
                    errorMsg = '<i class="fas fa-exclamation-circle me-1"></i>Fecha muy lejana (máx 5 años)';
                } else {
                    // Advertencia si está próxima a vencer (menos de 30 días)
                    const daysUntilExpiry = Math.floor((expiryDate - new Date()) / (1000 * 60 * 60 * 24));
                    if (daysUntilExpiry < 30) {
                        warningMsg = `<i class="fas fa-warning me-1"></i>Vence en ${daysUntilExpiry} días`;
                    }
                }
            }
        }
        
        // Actualizar visual
        if (isValid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        } else {
            field.classList.add('is-invalid');
            field.classList.remove('is-valid');
        }
        
        // Mostrar/ocultar mensaje de error
        let errorDiv = row.querySelector('.field-error-message');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'field-error-message small text-danger mt-1';
            field.parentElement.appendChild(errorDiv);
        }
        errorDiv.innerHTML = errorMsg;
        errorDiv.style.display = isValid && !errorMsg ? 'none' : 'block';
        
        // Mostrar/ocultar mensaje de advertencia
        let warningDiv = row.querySelector('.field-warning-message');
        if (warningMsg && !warningDiv) {
            warningDiv = document.createElement('div');
            warningDiv.className = 'field-warning-message small text-warning mt-1';
            field.parentElement.appendChild(warningDiv);
        }
        if (warningDiv) {
            warningDiv.innerHTML = warningMsg;
            warningDiv.style.display = warningMsg ? 'block' : 'none';
        }
        
        return isValid;
    }
    
    function validateForm() {
        let isValid = true;
        let errors = [];
        let errorsByRow = {};
        
        // Validar proveedor
        if (!proveedorSelect || !proveedorSelect.value) {
            isValid = false;
            errors.push('Selecciona un proveedor');
            proveedorSelect?.classList.add('is-invalid');
        } else {
            proveedorSelect?.classList.remove('is-invalid');
        }
        
        // Validar que haya al menos un producto
        const rows = detalleTable.querySelectorAll('tbody tr.formset-row');
        if (rows.length === 0) {
            isValid = false;
            errors.push('Agrega al menos un producto');
        }
        
        // Validar que cada producto tenga datos completos
        rows.forEach((row, index) => {
            const producto = row.querySelector('.producto-select');
            const cantidad = row.querySelector('.cantidad-input');
            const costo = row.querySelector('.costo-unitario-input');
            const fecha = row.querySelector('[type="date"]');
            
            let rowValid = true;
            let rowErrors = [];
            
            // Validar cada campo
            [producto, cantidad, costo, fecha].forEach(field => {
                if (field && !validateField(field)) {
                    rowValid = false;
                    isValid = false;
                }
            });
            
            // Marcar fila como válida o inválida
            if (rowValid) {
                row.classList.remove('table-danger', 'row-invalid');
                row.classList.add('row-valid');
            } else {
                row.classList.remove('row-valid');
                row.classList.add('table-danger', 'row-invalid');
            }
        });
        
        // Actualizar alerta de validación
        const alertDiv = document.getElementById('formValidationAlert');
        const errorsList = document.getElementById('formErrorsList');
        if (alertDiv && errorsList) {
            if (!isValid && errors.length > 0) {
                errorsList.innerHTML = errors.map(e => `<li>${e}</li>`).join('');
                alertDiv.style.display = 'block';
            } else {
                alertDiv.style.display = 'none';
            }
        }
        
        // Mostrar/ocultar botón de guardar
        if (guardarBtn) {
            guardarBtn.disabled = !isValid;
            guardarBtn.setAttribute('aria-disabled', !isValid);
        }
        
        return isValid;
    }
    
    // Validar en tiempo real - campo por campo con debounce
    let validationTimeout;
    
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('producto-select') ||
            e.target.classList.contains('cantidad-input') ||
            e.target.classList.contains('costo-unitario-input') ||
            e.target.type === 'date') {
            validateField(e.target);
            clearTimeout(validationTimeout);
            validationTimeout = setTimeout(validateForm, 200);
        }
    });
    
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('cantidad-input') ||
            e.target.classList.contains('costo-unitario-input')) {
            validateField(e.target);
            clearTimeout(validationTimeout);
            validationTimeout = setTimeout(validateForm, 300);
        }
    });
    
    // Validar al agregar/eliminar filas
    if (addRowBtn) {
        const originalClick = addRowBtn.onclick;
        addRowBtn.addEventListener('click', function() {
            setTimeout(validateForm, 100);
        });
    }
    
    // Confirmación antes de cancelar
    const cancelarBtn = document.getElementById('cancelarBtn');
    if (cancelarBtn) {
        cancelarBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Verificar si hay datos en el formulario
            const hasData = detalleTable.querySelectorAll('tbody tr.formset-row').length > 0 ||
                           (proveedorSelect && proveedorSelect.value);
            
            if (hasData) {
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
        });
    }
    
    // Manejo del envío del formulario
    if (form) {
        form.addEventListener('submit', function(e) {
            // Validar antes de enviar
            if (!validateForm()) {
                e.preventDefault();
                e.stopPropagation();
                
                // Recopilar errores
                let errorList = [];
                let errorCount = 0;
                
                if (!proveedorSelect || !proveedorSelect.value) {
                    errorList.push('<i class="fas fa-building me-2"></i>Selecciona un proveedor');
                    errorCount++;
                }
                
                const rows = detalleTable.querySelectorAll('tbody tr.formset-row');
                if (rows.length === 0) {
                    errorList.push('<i class="fas fa-box me-2"></i>Agrega al menos un producto');
                    errorCount++;
                } else {
                    rows.forEach((row, index) => {
                        if (row.classList.contains('table-danger')) {
                            const productName = row.querySelector('.producto-select')?.options[row.querySelector('.producto-select')?.selectedIndex]?.text || `Producto ${index + 1}`;
                            errorList.push(`<i class="fas fa-exclamation-triangle me-2"></i>Fila ${index + 1}: ${productName}`);
                            errorCount++;
                        }
                    });
                }
                
                const errorHtml = errorList.length > 0 
                    ? `<div class="text-start"><p class="mb-2"><strong>${errorCount} error(es):</strong></p><ul class="list-unstyled">${errorList.map(e => `<li class="mb-2">${e}</li>`).join('')}</ul></div>`
                    : '<p>Por favor revisa los campos marcados en rojo</p>';
                
                Swal.fire({
                    icon: 'error',
                    title: 'No se puede guardar',
                    html: errorHtml,
                    confirmButtonText: 'Entendido',
                    didOpen: () => {
                        // Scroll al primer error
                        const firstError = document.querySelector('.table-danger');
                        if (firstError) {
                            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }
                    }
                });
            } else {
                // Mostrar loader en el botón mientras se envía
                const originalHtml = guardarBtn.innerHTML;
                guardarBtn.disabled = true;
                guardarBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Guardando...';
                
                // Restaurar después de envío (el servidor redirigirá)
                setTimeout(() => {
                    guardarBtn.innerHTML = originalHtml;
                    guardarBtn.disabled = false;
                }, 3000);
            }
        });
    }
    
    // Initial validation
    validateForm();
    
    // Initial calculation
    calculateTotals();
});
