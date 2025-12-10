/**
 * Sistema de Gestión de Mesas para el POS
 */

class GestionMesas {
    constructor() {
        this.mesaSeleccionada = null;
        this.inicializar();
    }

    inicializar() {
        // Cargar mesas cuando se abre el modal
        const modalMesas = document.getElementById('modalMesas');
        if (modalMesas) {
            modalMesas.addEventListener('show.bs.modal', () => {
                this.cargarMesas();
            });
        }

        // Recuperar mesa activa del localStorage
        const mesaActiva = localStorage.getItem('mesa_activa');
        if (mesaActiva) {
            this.mesaSeleccionada = parseInt(mesaActiva);
            this.recuperarInfoMesa(this.mesaSeleccionada);
        }
    }

    async recuperarInfoMesa(mesaId) {
        try {
            const response = await fetch('/pos/api/mesas/');
            const data = await response.json();

            if (data.success) {
                const mesa = data.mesas.find(m => m.id === mesaId);
                if (mesa && mesa.cuenta_abierta) {
                    this.mostrarIndicadorMesa(mesaId, mesa.nombre);
                } else {
                    // La mesa ya no está activa, limpiar
                    localStorage.removeItem('mesa_activa');
                    this.mesaSeleccionada = null;
                }
            }
        } catch (error) {
            console.error('Error al recuperar info de mesa:', error);
        }
    }

    async cargarMesas() {
        try {
            const response = await fetch('/pos/api/mesas/');
            const data = await response.json();

            if (data.success) {
                this.mostrarMesas(data.mesas);
            }
        } catch (error) {
            console.error('Error al cargar mesas:', error);
        }
    }

    mostrarMesas(mesas) {
        const container = document.getElementById('mesas-container');
        container.innerHTML = '';

        // Botón para crear nueva mesa
        const btnNuevaMesa = `
            <div class="col-md-3">
                <div class="card mesa-card mesa-nueva" onclick="gestionMesas.mostrarModalCrearMesa()">
                    <div class="card-body text-center">
                        <div class="mesa-icon mb-2">
                            <i class="bi bi-plus-circle fs-1 text-primary"></i>
                        </div>
                        <h5 class="card-title">Nueva Mesa</h5>
                        <p class="text-muted mb-0">Crear mesa</p>
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', btnNuevaMesa);

        mesas.forEach(mesa => {
            const estadoClass = mesa.cuenta_abierta ? 'ocupada' : 'disponible';
            const estadoIcon = mesa.cuenta_abierta ? 'bi-door-closed-fill' : 'bi-door-open-fill';
            const estadoColor = mesa.cuenta_abierta ? 'danger' : 'success';

            const mesaHTML = `
                <div class="col-md-3">
                    <div class="card mesa-card mesa-${estadoClass}" data-mesa-id="${mesa.id}">
                        <div class="card-body text-center">
                            <div class="mesa-icon mb-2">
                                <i class="bi ${estadoIcon} fs-1 text-${estadoColor}"></i>
                            </div>
                            <h5 class="card-title">${mesa.nombre}</h5>

                            ${mesa.cuenta_abierta ? `
                                <div class="alert alert-warning py-2 mb-2">
                                    <strong>Total: $${this.formatearMoneda(mesa.total_cuenta)}</strong>
                                    ${mesa.cliente ? `<br><small>${mesa.cliente.nombre}</small>` : ''}
                                </div>
                                <button class="btn btn-sm btn-info w-100 mb-1" onclick="gestionMesas.seleccionarMesa(${mesa.id}, '${mesa.nombre}')">
                                    <i class="bi bi-cursor me-1"></i>Seleccionar Mesa
                                </button>
                                <button class="btn btn-sm btn-primary w-100 mb-1" onclick="gestionMesas.verCuenta(${mesa.id})">
                                    <i class="bi bi-eye me-1"></i>Ver Cuenta
                                </button>
                                <button class="btn btn-sm btn-success w-100" onclick="gestionMesas.cerrarMesa(${mesa.id})">
                                    <i class="bi bi-check-circle me-1"></i>Cerrar Mesa
                                </button>
                            ` : `
                                <button class="btn btn-success w-100 mb-1" onclick="gestionMesas.abrirMesa(${mesa.id})">
                                    <i class="bi bi-door-open me-1"></i>Abrir Mesa
                                </button>
                                <div class="btn-group w-100" role="group">
                                    <button class="btn btn-sm btn-outline-primary" onclick="gestionMesas.editarMesa(${mesa.id}, '${mesa.nombre}')" title="Editar">
                                        <i class="bi bi-pencil"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger" onclick="gestionMesas.eliminarMesa(${mesa.id}, '${mesa.nombre}')" title="Eliminar">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                </div>
                            `}
                        </div>
                    </div>
                </div>
            `;

            container.insertAdjacentHTML('beforeend', mesaHTML);
        });
    }

    async abrirMesa(mesaId) {
        // Cerrar modal de mesas
        const modalMesas = bootstrap.Modal.getInstance(document.getElementById('modalMesas'));
        modalMesas.hide();

        // Abrir la mesa con el cliente seleccionado
        const clienteSelect = document.getElementById('cliente-select');
        const clienteId = clienteSelect.value || 1;

        try {
            const response = await fetch(`/pos/api/mesa/${mesaId}/abrir/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.obtenerCSRFToken()
                },
                body: JSON.stringify({ cliente_id: clienteId })
            });

            const data = await response.json();

            if (data.success) {
                this.mesaSeleccionada = mesaId;
                
                // Guardar en localStorage
                localStorage.setItem('mesa_activa', mesaId);
                
                // Mostrar indicador de mesa activa
                this.mostrarIndicadorMesa(mesaId, data.mesa_numero);
                
                // Mostrar notificación
                this.mostrarNotificacion(`Mesa ${data.mesa_numero} abierta. Los productos se agregarán a esta mesa.`, 'success');
            } else {
                alert('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al abrir la mesa');
        }
    }

    mostrarIndicadorMesa(mesaId, mesaNombre) {
        // Remover indicador anterior si existe
        const indicadorAnterior = document.getElementById('indicador-mesa');
        if (indicadorAnterior) {
            indicadorAnterior.remove();
        }

        // Agregar indicador visual fijo en la parte superior
        const indicador = document.createElement('div');
        indicador.id = 'indicador-mesa';
        indicador.className = 'indicador-mesa-fijo';
        indicador.innerHTML = `
            <div class="container-fluid">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center">
                        <i class="bi bi-door-closed-fill me-2 fs-4"></i>
                        <div>
                            <strong class="fs-5">${mesaNombre} Activa</strong>
                            <br>
                            <small>Los productos se agregarán a esta mesa</small>
                        </div>
                    </div>
                    <div>
                        <button class="btn btn-light me-2" onclick="gestionMesas.verCuenta(${mesaId})">
                            <i class="bi bi-eye me-1"></i>Ver Cuenta
                        </button>
                        <button class="btn btn-warning me-2" onclick="event.stopPropagation(); document.getElementById('modalMesas').dispatchEvent(new Event('show.bs.modal')); bootstrap.Modal.getOrCreateInstance(document.getElementById('modalMesas')).show();">
                            <i class="bi bi-arrow-left-right me-1"></i>Cambiar Mesa
                        </button>
                        <button class="btn btn-danger" onclick="gestionMesas.desactivarMesa()">
                            <i class="bi bi-x-circle me-1"></i>Desactivar
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Insertar al inicio del body
        document.body.insertBefore(indicador, document.body.firstChild);
        
        // Agregar padding al contenido para que no quede oculto
        document.body.style.paddingTop = '80px';
    }

    seleccionarMesa(mesaId, mesaNombre) {
        // Cerrar modal de mesas
        const modalMesas = bootstrap.Modal.getInstance(document.getElementById('modalMesas'));
        if (modalMesas) {
            modalMesas.hide();
        }

        this.mesaSeleccionada = mesaId;
        localStorage.setItem('mesa_activa', mesaId);
        this.mostrarIndicadorMesa(mesaId, mesaNombre);
        this.mostrarNotificacion(`${mesaNombre} seleccionada. Los productos se agregarán a esta mesa.`, 'success');
    }

    desactivarMesa() {
        if (confirm('¿Desea desactivar la mesa actual? Los productos en el carrito no se perderán.')) {
            this.mesaSeleccionada = null;
            localStorage.removeItem('mesa_activa');
            
            const indicador = document.getElementById('indicador-mesa');
            if (indicador) {
                indicador.remove();
            }
            
            // Remover padding del body
            document.body.style.paddingTop = '0';
            
            this.mostrarNotificacion('Mesa desactivada. Ahora puedes hacer ventas normales.', 'info');
        }
    }

    mostrarNotificacion(mensaje, tipo = 'info') {
        const alertaHTML = `
            <div class="alert alert-${tipo} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3" style="z-index: 9999;" role="alert">
                ${mensaje}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', alertaHTML);

        const alerta = document.querySelector('.alert');
        setTimeout(() => {
            alerta.remove();
        }, 4000);
    }

    async verCuenta(mesaId) {
        try {
            const response = await fetch(`/pos/api/mesa/${mesaId}/items/`);
            const data = await response.json();

            if (data.success) {
                this.mostrarModalCuenta(mesaId, data.items, data.total);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    mostrarModalCuenta(mesaId, items, total) {
        let itemsHTML = '';
        items.forEach(item => {
            const anotacionEscapada = item.anotacion ? item.anotacion.replace(/'/g, "\\'").replace(/"/g, '&quot;') : '';
            itemsHTML += `
                <tr>
                    <td>
                        ${item.producto}
                        ${item.anotacion ? `<br><small class="text-muted"><i class="bi bi-chat-left-text me-1"></i>${item.anotacion}</small>` : ''}
                    </td>
                    <td class="text-center">${item.cantidad}</td>
                    <td class="text-end">$${this.formatearMoneda(item.precio_unitario)}</td>
                    <td class="text-end"><strong>$${this.formatearMoneda(item.subtotal)}</strong></td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-warning me-1" onclick="gestionMesas.editarAnotacion(${mesaId}, ${item.id}, '${anotacionEscapada}')" title="Editar comentario">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="gestionMesas.eliminarItem(${mesaId}, ${item.id})" title="Eliminar">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        });

        const modalHTML = `
            <div class="modal fade" id="modalCuentaMesa" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title"><i class="bi bi-receipt me-2"></i>Cuenta de Mesa</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Producto</th>
                                        <th class="text-center">Cant.</th>
                                        <th class="text-end">Precio</th>
                                        <th class="text-end">Subtotal</th>
                                        <th class="text-center">Acciones</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${itemsHTML}
                                </tbody>
                                <tfoot>
                                    <tr class="table-primary">
                                        <th colspan="3" class="text-end">TOTAL:</th>
                                        <th class="text-end">$${this.formatearMoneda(total)}</th>
                                        <th></th>
                                    </tr>
                                </tfoot>
                            </table>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="bi bi-x-circle me-1"></i>Cerrar
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remover modal anterior
        const modalAnterior = document.getElementById('modalCuentaMesa');
        if (modalAnterior) {
            modalAnterior.remove();
        }

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('modalCuentaMesa'));
        modal.show();
    }

    async cerrarMesa(mesaId) {
        // Obtener datos de la mesa primero
        try {
            const response = await fetch(`/pos/api/mesa/${mesaId}/items/`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();

            if (data.success) {
                // Mostrar modal de confirmación con detalles de la mesa
                this.mostrarModalCerrarMesa(mesaId, data.items, data.total, data.mesa_numero);
            } else {
                this.mostrarNotificacion('Error: ' + (data.error || 'No se pudieron cargar los items'), 'error');
            }
        } catch (error) {
            console.error('Error completo:', error);
            this.mostrarNotificacion('Error al cargar los datos de la mesa: ' + error.message, 'error');
        }
    }

    mostrarModalCerrarMesa(mesaId, items, total, mesaNombre) {
        // Crear lista de items para mostrar
        let itemsHTML = '';
        if (items && items.length > 0) {
            itemsHTML = items.map(item => `
                <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                    <div>
                        <strong>${item.producto}</strong>
                        ${item.anotacion ? `<br><small class="text-muted"><i class="bi bi-chat-left-text me-1"></i>${item.anotacion}</small>` : ''}
                    </div>
                    <div class="text-end">
                        <span class="badge bg-primary me-2">${item.cantidad}</span>
                        <strong>${this.formatearMoneda(item.subtotal)}</strong>
                    </div>
                </div>
            `).join('');
        } else {
            itemsHTML = '<div class="text-center text-muted py-4"><i class="bi bi-cart-x fs-1 mb-2 d-block"></i>No hay productos en esta mesa</div>';
        }

        const modalHTML = `
            <div class="modal fade" id="modalCerrarMesa" tabindex="-1">
                <div class="modal-dialog modal-lg modal-dialog-centered">
                    <div class="modal-content border-0 shadow-lg">
                        <div class="modal-header bg-success text-white border-0">
                            <h5 class="modal-title">
                                <i class="bi bi-check-circle-fill me-2"></i>Cerrar Mesa y Generar Factura
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="text-center mb-4">
                                <div class="bg-light rounded-circle d-inline-flex align-items-center justify-content-center mb-3" style="width: 80px; height: 80px;">
                                    <i class="bi bi-receipt text-success" style="font-size: 2.5rem;"></i>
                                </div>
                                <h4 class="text-dark mb-2">${mesaNombre || 'Mesa'}</h4>
                                <p class="text-muted">¿Desea cerrar esta mesa y generar la factura?</p>
                            </div>

                            <div class="card border-0 bg-light mb-4">
                                <div class="card-header bg-transparent border-0 pb-0">
                                    <h6 class="mb-0 text-dark">
                                        <i class="bi bi-list-ul me-2"></i>Resumen de Productos
                                    </h6>
                                </div>
                                <div class="card-body pt-2" style="max-height: 300px; overflow-y: auto;">
                                    ${itemsHTML}
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-6">
                                    <div class="card border-0 bg-primary text-white">
                                        <div class="card-body text-center">
                                            <i class="bi bi-currency-dollar fs-1 mb-2"></i>
                                            <h3 class="mb-0">${this.formatearMoneda(total)}</h3>
                                            <small>Total a Facturar</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card border-0 bg-info text-white">
                                        <div class="card-body text-center">
                                            <i class="bi bi-receipt-cutoff fs-1 mb-2"></i>
                                            <h5 class="mb-0">Factura</h5>
                                            <small>Se generará automáticamente</small>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            ${items.length === 0 ? `
                                <div class="alert alert-warning border-0 mt-3">
                                    <i class="bi bi-exclamation-triangle me-2"></i>
                                    <strong>Atención:</strong> Esta mesa no tiene productos. Se cerrará sin generar factura.
                                </div>
                            ` : `
                                <div class="alert alert-warning border-0 mt-3">
                                    <i class="bi bi-exclamation-triangle me-2"></i>
                                    <strong>Importante:</strong> Al cerrar la mesa se generará la factura y la mesa será eliminada permanentemente.
                                </div>
                            `}
                        </div>
                        <div class="modal-footer border-0 justify-content-center">
                            <button type="button" class="btn btn-light btn-lg px-4 me-3" data-bs-dismiss="modal">
                                <i class="bi bi-x-circle me-1"></i>Cancelar
                            </button>
                            <button type="button" class="btn btn-success btn-lg px-4" onclick="gestionMesas.confirmarCerrarMesa(${mesaId})">
                                <i class="bi bi-check-circle-fill me-1"></i>Cerrar y Eliminar Mesa
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remover modal anterior si existe
        const modalAnterior = document.getElementById('modalCerrarMesa');
        if (modalAnterior) modalAnterior.remove();

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('modalCerrarMesa'));
        modal.show();
    }

    async confirmarCerrarMesa(mesaId) {
        // Mostrar loading en el botón
        const btnCerrar = document.querySelector('#modalCerrarMesa .btn-success');
        const textoOriginal = btnCerrar.innerHTML;
        btnCerrar.disabled = true;
        btnCerrar.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Cerrando y Eliminando...';

        try {
            // Obtener datos de la mesa nuevamente
            const response = await fetch(`/pos/api/mesa/${mesaId}/items/`);
            const data = await response.json();

            if (data.success) {
                // Guardar el ID de la mesa para usarlo después
                this.mesaParaCerrar = mesaId;
                
                // Cargar items en el carrito
                this.cargarItemsEnCarrito(data.items);
                
                // Cerrar modal actual
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalCerrarMesa'));
                modal.hide();
                
                // Mostrar el modal de pago usando la función del carrito
                if (window.carritoPOS) {
                    window.carritoPOS.mostrarFormularioPago();
                    
                    // Modificar el botón de procesar para que cierre la mesa
                    setTimeout(() => {
                        const btnProcesar = document.querySelector('#modalCompletarVenta .btn-success');
                        if (btnProcesar) {
                            btnProcesar.onclick = () => this.procesarCierreMesaConCarrito(mesaId);
                        }
                    }, 100);
                } else {
                    this.mostrarNotificacion('Error: El sistema de carrito no está disponible', 'error');
                    btnCerrar.disabled = false;
                    btnCerrar.innerHTML = textoOriginal;
                }
            } else {
                this.mostrarNotificacion('Error: ' + (data.error || 'No se pudieron cargar los items'), 'error');
                btnCerrar.disabled = false;
                btnCerrar.innerHTML = textoOriginal;
            }
        } catch (error) {
            console.error('Error completo:', error);
            this.mostrarNotificacion('Error al procesar el cierre de mesa: ' + error.message, 'error');
            btnCerrar.disabled = false;
            btnCerrar.innerHTML = textoOriginal;
        }
    }

    cargarItemsEnCarrito(items) {
        // Limpiar carrito actual
        if (window.carritoPOS) {
            window.carritoPOS.carrito = [];
            
            // Agregar items de la mesa al carrito
            items.forEach(item => {
                window.carritoPOS.carrito.push({
                    producto_id: item.producto_id,
                    nombre: item.producto,
                    precio: parseFloat(item.precio_unitario),
                    cantidad: item.cantidad,
                    lote_id: item.lote_id,
                    max_stock: item.cantidad // Ya están en la mesa, no hay límite adicional
                });
            });
            
            // Actualizar vista del carrito
            window.carritoPOS.actualizarVistaCarrito();
        }
    }

    async procesarCierreMesaConCarrito(mesaId) {
        const metodoPago = document.getElementById('metodo-pago').value;
        const montoRecibido = parseFloat(document.getElementById('monto-recibido').value) || 0;
        const clienteId = document.getElementById('cliente-modal').value;

        console.log('Datos a enviar:', {
            metodo_pago: metodoPago,
            monto_recibido: montoRecibido,
            cliente_id: clienteId
        });

        if (!metodoPago) {
            alert('Por favor seleccione un método de pago');
            return;
        }

        if (!clienteId) {
            alert('Por favor seleccione un cliente');
            return;
        }

        try {
            const response = await fetch(`/pos/api/mesa/${mesaId}/cerrar/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.obtenerCSRFToken()
                },
                body: JSON.stringify({ 
                    metodo_pago: metodoPago,
                    monto_recibido: montoRecibido,
                    cliente_id: clienteId
                })
            });

            const data = await response.json();

            if (data.success) {
                // Cerrar modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalCompletarVenta'));
                if (modal) modal.hide();

                // Limpiar mesa activa si es la que se cerró
                if (this.mesaSeleccionada === mesaId) {
                    this.mesaSeleccionada = null;
                    localStorage.removeItem('mesa_activa');
                    const indicador = document.getElementById('indicador-mesa');
                    if (indicador) {
                        indicador.remove();
                    }
                    // Remover padding del body
                    document.body.style.paddingTop = '0';
                }

                // Limpiar carrito
                if (window.carritoPOS) {
                    window.carritoPOS.vaciarCarrito();
                }

                this.mostrarNotificacion(data.mensaje, 'success');
                this.cargarMesas();
                
                // Mostrar modal para ver factura
                setTimeout(() => {
                    this.mostrarModalVerFactura(data.venta_id);
                }, 500);
            } else {
                alert('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al cerrar la mesa');
        }
    }

    mostrarModalCompletarVenta(mesaId, total, items) {
        const modalHTML = `
            <div class="modal fade" id="modalCompletarVenta" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-success text-white">
                            <h5 class="modal-title">
                                <i class="bi bi-check-circle me-2"></i>Completar Venta - Mesa
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6 class="mb-3"><i class="bi bi-receipt me-2"></i>Resumen de la Cuenta</h6>
                                    <div class="table-responsive" style="max-height: 300px; overflow-y: auto;">
                                        <table class="table table-sm">
                                            <thead>
                                                <tr>
                                                    <th>Producto</th>
                                                    <th class="text-center">Cant.</th>
                                                    <th class="text-end">Subtotal</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${items.map(item => `
                                                    <tr>
                                                        <td>
                                                            ${item.producto}
                                                            ${item.anotacion ? `<br><small class="text-muted">${item.anotacion}</small>` : ''}
                                                        </td>
                                                        <td class="text-center">${item.cantidad}</td>
                                                        <td class="text-end">$${this.formatearMoneda(item.subtotal)}</td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                            <tfoot>
                                                <tr class="table-success">
                                                    <th colspan="2" class="text-end">TOTAL:</th>
                                                    <th class="text-end">$${this.formatearMoneda(total)}</th>
                                                </tr>
                                            </tfoot>
                                        </table>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <h6 class="mb-3"><i class="bi bi-credit-card me-2"></i>Información de Pago</h6>
                                    <form id="formCompletarVenta">
                                        <div class="mb-3">
                                            <label for="metodo-pago" class="form-label">Método de Pago *</label>
                                            <select class="form-select" id="metodo-pago" required>
                                                <option value="efectivo">Efectivo</option>
                                                <option value="tarjeta_debito">Tarjeta Débito</option>
                                                <option value="tarjeta_credito">Tarjeta Crédito</option>
                                                <option value="transferencia">Transferencia</option>
                                            </select>
                                        </div>
                                        <div class="mb-3">
                                            <label for="monto-recibido" class="form-label">Monto Recibido</label>
                                            <input type="number" class="form-control" id="monto-recibido" 
                                                   step="0.01" min="${total}" value="${total}" 
                                                   placeholder="Ingrese el monto recibido">
                                            <small class="text-muted">Total a pagar: $${this.formatearMoneda(total)}</small>
                                        </div>
                                        <div class="mb-3" id="cambio-container" style="display: none;">
                                            <div class="alert alert-info">
                                                <strong>Cambio a devolver:</strong> 
                                                <span id="cambio-valor" class="fs-5">$0.00</span>
                                            </div>
                                        </div>
                                        <div class="mb-3">
                                            <label for="observaciones-venta" class="form-label">Observaciones</label>
                                            <textarea class="form-control" id="observaciones-venta" rows="2" 
                                                      placeholder="Observaciones adicionales (opcional)"></textarea>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="bi bi-x-circle me-1"></i>Cancelar
                            </button>
                            <button type="button" class="btn btn-success" onclick="gestionMesas.procesarCierreMesa(${mesaId})">
                                <i class="bi bi-check-circle-fill me-1"></i>Generar Factura
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remover modal anterior
        const modalAnterior = document.getElementById('modalCompletarVenta');
        if (modalAnterior) modalAnterior.remove();

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('modalCompletarVenta'));
        modal.show();

        // Calcular cambio automáticamente
        const montoRecibidoInput = document.getElementById('monto-recibido');
        const cambioContainer = document.getElementById('cambio-container');
        const cambioValor = document.getElementById('cambio-valor');

        montoRecibidoInput.addEventListener('input', () => {
            const montoRecibido = parseFloat(montoRecibidoInput.value) || 0;
            const cambio = montoRecibido - total;
            
            if (cambio > 0) {
                cambioContainer.style.display = 'block';
                cambioValor.textContent = '$' + this.formatearMoneda(cambio);
            } else {
                cambioContainer.style.display = 'none';
            }
        });
    }

    async procesarCierreMesa(mesaId) {
        const metodoPago = document.getElementById('metodo-pago').value;
        const montoRecibido = parseFloat(document.getElementById('monto-recibido').value) || 0;
        const observaciones = document.getElementById('observaciones-venta').value;

        if (!metodoPago) {
            alert('Por favor seleccione un método de pago');
            return;
        }

        try {
            const response = await fetch(`/pos/api/mesa/${mesaId}/cerrar/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.obtenerCSRFToken()
                },
                body: JSON.stringify({ 
                    metodo_pago: metodoPago,
                    monto_recibido: montoRecibido,
                    observaciones: observaciones
                })
            });

            const data = await response.json();

            if (data.success) {
                // Cerrar modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalCompletarVenta'));
                if (modal) modal.hide();

                // Limpiar mesa activa si es la que se cerró
                if (this.mesaSeleccionada === mesaId) {
                    this.mesaSeleccionada = null;
                    localStorage.removeItem('mesa_activa');
                    const indicador = document.getElementById('indicador-mesa');
                    if (indicador) {
                        indicador.remove();
                    }
                    // Remover padding del body
                    document.body.style.paddingTop = '0';
                }

                this.mostrarNotificacion(data.mensaje, 'success');
                this.cargarMesas();
                
                // Mostrar modal para ver factura
                setTimeout(() => {
                    this.mostrarModalVerFactura(data.venta_id);
                }, 500);
            } else {
                alert('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al cerrar la mesa');
        }
    }

    mostrarModalCrearMesa() {
        const modalHTML = `
            <div class="modal fade" id="modalCrearMesa" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title">
                                <i class="bi bi-plus-circle me-2"></i>Crear Nueva Mesa
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-info">
                                <i class="bi bi-info-circle me-2"></i>
                                <strong>El número de mesa se asignará automáticamente.</strong>
                                Solo necesitas especificar el nombre y características.
                            </div>
                            <form id="formCrearMesa">
                                <div class="mb-3">
                                    <label for="nombre-mesa" class="form-label">Nombre de la Mesa</label>
                                    <input type="text" class="form-control" id="nombre-mesa" placeholder="Ej: Mesa Principal, Terraza 1, VIP..." autofocus>
                                    <small class="text-muted">Si no especificas un nombre, se generará automáticamente</small>
                                </div>
                                <div class="mb-3">
                                    <label for="descripcion-mesa" class="form-label">Descripción (opcional)</label>
                                    <input type="text" class="form-control" id="descripcion-mesa" placeholder="Ej: Junto a la ventana, Vista al jardín...">
                                    <small class="text-muted">Información adicional sobre ubicación o características</small>
                                </div>

                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-primary" onclick="gestionMesas.crearMesa()">
                                <i class="bi bi-check-circle me-1"></i>Crear Mesa
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const modalAnterior = document.getElementById('modalCrearMesa');
        if (modalAnterior) modalAnterior.remove();

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('modalCrearMesa'));
        modal.show();
    }

    async crearMesa() {
        const nombre = document.getElementById('nombre-mesa').value.trim();
        const descripcion = document.getElementById('descripcion-mesa').value.trim();

        try {
            const response = await fetch('/pos/api/mesa/crear/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.obtenerCSRFToken()
                },
                body: JSON.stringify({ nombre, descripcion })
            });

            const data = await response.json();

            if (data.success) {
                this.mostrarNotificacion(data.mensaje, 'success');
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalCrearMesa'));
                modal.hide();
                this.cargarMesas();
            } else {
                alert('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al crear la mesa');
        }
    }

    editarMesa(mesaId, nombre) {
        const modalHTML = `
            <div class="modal fade" id="modalEditarMesa" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-warning">
                            <h5 class="modal-title">
                                <i class="bi bi-pencil me-2"></i>Editar Mesa
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-info">
                                <i class="bi bi-info-circle me-2"></i>
                                Solo puedes cambiar el nombre de la mesa.
                            </div>
                            <form id="formEditarMesa">
                                <div class="mb-3">
                                    <label for="edit-nombre-mesa" class="form-label">Nombre de la Mesa</label>
                                    <input type="text" class="form-control" id="edit-nombre-mesa" value="${nombre}" autofocus>
                                </div>
                                <div class="mb-3">
                                    <label for="edit-descripcion-mesa" class="form-label">Descripción (opcional)</label>
                                    <input type="text" class="form-control" id="edit-descripcion-mesa" placeholder="Agregar descripción...">
                                    <small class="text-muted">Se agregará entre paréntesis al nombre</small>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-warning" onclick="gestionMesas.guardarEdicionMesa(${mesaId})">
                                <i class="bi bi-check-circle me-1"></i>Guardar Cambios
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const modalAnterior = document.getElementById('modalEditarMesa');
        if (modalAnterior) modalAnterior.remove();

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('modalEditarMesa'));
        modal.show();
    }

    async guardarEdicionMesa(mesaId) {
        const nombre = document.getElementById('edit-nombre-mesa').value.trim();
        const descripcion = document.getElementById('edit-descripcion-mesa').value.trim();

        if (!nombre) {
            alert('El nombre de la mesa es obligatorio');
            return;
        }

        try {
            const response = await fetch(`/pos/api/mesa/${mesaId}/editar/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.obtenerCSRFToken()
                },
                body: JSON.stringify({ nombre, descripcion })
            });

            const data = await response.json();

            if (data.success) {
                this.mostrarNotificacion(data.mensaje, 'success');
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalEditarMesa'));
                modal.hide();
                this.cargarMesas();
            } else {
                alert('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al editar la mesa');
        }
    }

    eliminarMesa(mesaId, nombre) {
        this.mostrarModalEliminar(mesaId, nombre);
    }

    mostrarModalEliminar(mesaId, nombre) {
        const modalHTML = `
            <div class="modal fade" id="modalEliminarMesa" tabindex="-1">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-0 shadow-lg">
                        <div class="modal-header bg-danger text-white border-0">
                            <h5 class="modal-title">
                                <i class="bi bi-exclamation-triangle-fill me-2"></i>Confirmar Eliminación
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body text-center py-4">
                            <div class="mb-4">
                                <i class="bi bi-trash3-fill text-danger" style="font-size: 4rem;"></i>
                            </div>
                            <h4 class="mb-3 text-dark">¿Eliminar Mesa?</h4>
                            <p class="text-muted mb-4">
                                Estás a punto de eliminar <strong>"${nombre}"</strong>
                                <br>
                                <small class="text-warning">
                                    <i class="bi bi-exclamation-circle me-1"></i>
                                    Esta acción no se puede deshacer
                                </small>
                            </p>
                            <div class="alert alert-warning border-0 bg-light">
                                <i class="bi bi-info-circle me-2"></i>
                                <strong>Nota:</strong> Solo se desactivará la mesa, no se eliminará permanentemente
                            </div>
                        </div>
                        <div class="modal-footer border-0 justify-content-center">
                            <button type="button" class="btn btn-light btn-lg px-4 me-3" data-bs-dismiss="modal">
                                <i class="bi bi-x-circle me-1"></i>Cancelar
                            </button>
                            <button type="button" class="btn btn-danger btn-lg px-4" onclick="gestionMesas.confirmarEliminarMesa(${mesaId})">
                                <i class="bi bi-trash3 me-1"></i>Sí, Eliminar
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remover modal anterior si existe
        const modalAnterior = document.getElementById('modalEliminarMesa');
        if (modalAnterior) modalAnterior.remove();

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('modalEliminarMesa'));
        modal.show();
    }

    async confirmarEliminarMesa(mesaId) {
        // Mostrar loading en el botón
        const btnEliminar = document.querySelector('#modalEliminarMesa .btn-danger');
        const textoOriginal = btnEliminar.innerHTML;
        btnEliminar.disabled = true;
        btnEliminar.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Eliminando...';

        try {
            const response = await fetch(`/pos/api/mesa/${mesaId}/eliminar/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.obtenerCSRFToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                // Cerrar modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalEliminarMesa'));
                modal.hide();
                
                this.mostrarNotificacion(data.mensaje, 'success');
                this.cargarMesas();
            } else {
                this.mostrarNotificacion('Error: ' + data.error, 'error');
                btnEliminar.disabled = false;
                btnEliminar.innerHTML = textoOriginal;
            }
        } catch (error) {
            console.error('Error:', error);
            this.mostrarNotificacion('Error al eliminar la mesa', 'error');
            btnEliminar.disabled = false;
            btnEliminar.innerHTML = textoOriginal;
        }
    }

    async editarAnotacion(mesaId, itemId, anotacionActual) {
        const nuevaAnotacion = prompt('Editar comentario:', anotacionActual);
        
        if (nuevaAnotacion === null) return; // Usuario canceló
        
        try {
            const response = await fetch(`/pos/api/mesa/${mesaId}/item/${itemId}/editar/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.obtenerCSRFToken()
                },
                body: JSON.stringify({ anotacion: nuevaAnotacion })
            });

            const data = await response.json();

            if (data.success) {
                this.mostrarNotificacion('Comentario actualizado correctamente', 'success');
                // Cerrar modal actual y recargar
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalCuentaMesa'));
                if (modal) modal.hide();
                // Recargar la cuenta
                setTimeout(() => this.verCuenta(mesaId), 300);
            } else {
                alert('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al editar el comentario');
        }
    }

    async eliminarItem(mesaId, itemId) {
        if (!confirm('¿Está seguro de eliminar este producto de la mesa?')) {
            return;
        }

        try {
            const response = await fetch(`/pos/api/mesa/${mesaId}/item/${itemId}/eliminar/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.obtenerCSRFToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                this.mostrarNotificacion('Producto eliminado correctamente', 'success');
                // Cerrar modal actual y recargar
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalCuentaMesa'));
                if (modal) modal.hide();
                // Recargar la cuenta
                setTimeout(() => this.verCuenta(mesaId), 300);
            } else {
                alert('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al eliminar el producto');
        }
    }

    formatearMoneda(valor) {
        return parseFloat(valor).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    mostrarModalVerFactura(ventaId) {
        const modalHTML = `
            <div class="modal fade" id="modalVerFactura" tabindex="-1">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-0 shadow-lg">
                        <div class="modal-header bg-info text-white border-0">
                            <h5 class="modal-title">
                                <i class="bi bi-receipt-cutoff me-2"></i>Mesa Cerrada y Eliminada
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body text-center py-4">
                            <div class="mb-4">
                                <div class="bg-success rounded-circle d-inline-flex align-items-center justify-content-center mb-3" style="width: 80px; height: 80px;">
                                    <i class="bi bi-check-lg text-white" style="font-size: 2.5rem;"></i>
                                </div>
                                <h4 class="text-success mb-2">¡Mesa Cerrada y Eliminada!</h4>
                                <p class="text-muted mb-0">La mesa ha sido cerrada, eliminada y la factura ha sido generada correctamente.</p>
                            </div>
                            
                            <div class="alert alert-info border-0 bg-light">
                                <i class="bi bi-info-circle me-2"></i>
                                <strong>Factura #${ventaId}</strong> generada exitosamente
                            </div>

                            <div class="d-flex justify-content-center gap-3 mt-4">
                                <div class="text-center">
                                    <i class="bi bi-eye-fill text-primary fs-1 mb-2"></i>
                                    <p class="small text-muted mb-0">Ver Detalles</p>
                                </div>
                                <div class="text-center">
                                    <i class="bi bi-printer-fill text-secondary fs-1 mb-2"></i>
                                    <p class="small text-muted mb-0">Imprimir</p>
                                </div>
                                <div class="text-center">
                                    <i class="bi bi-download text-success fs-1 mb-2"></i>
                                    <p class="small text-muted mb-0">Descargar</p>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer border-0 justify-content-center">
                            <button type="button" class="btn btn-light btn-lg px-4 me-3" data-bs-dismiss="modal">
                                <i class="bi bi-x-circle me-1"></i>Continuar
                            </button>
                            <button type="button" class="btn btn-info btn-lg px-4" onclick="gestionMesas.verFactura(${ventaId})">
                                <i class="bi bi-receipt me-1"></i>Ver Factura
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remover modal anterior si existe
        const modalAnterior = document.getElementById('modalVerFactura');
        if (modalAnterior) modalAnterior.remove();

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('modalVerFactura'));
        modal.show();
    }

    verFactura(ventaId) {
        // Cerrar modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('modalVerFactura'));
        if (modal) modal.hide();
        
        // Redirigir a la factura
        window.location.href = `/pos/venta/${ventaId}/`;
    }

    obtenerCSRFToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Inicializar cuando el documento esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.gestionMesas = new GestionMesas();
});
