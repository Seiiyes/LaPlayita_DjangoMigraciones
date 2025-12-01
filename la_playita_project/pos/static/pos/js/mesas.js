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
                    this.mostrarIndicadorMesa(mesaId, mesa.numero);
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
                            <p class="text-muted mb-2">
                                <i class="bi bi-people me-1"></i>${mesa.capacidad} personas
                            </p>
                            ${mesa.cuenta_abierta ? `
                                <div class="alert alert-warning py-2 mb-2">
                                    <strong>Total: $${this.formatearMoneda(mesa.total_cuenta)}</strong>
                                    ${mesa.cliente ? `<br><small>${mesa.cliente.nombre}</small>` : ''}
                                </div>
                                <button class="btn btn-sm btn-info w-100 mb-1" onclick="gestionMesas.seleccionarMesa(${mesa.id}, '${mesa.numero}')">
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
                                    <button class="btn btn-sm btn-outline-primary" onclick="gestionMesas.editarMesa(${mesa.id}, '${mesa.numero}', '${mesa.nombre}', ${mesa.capacidad})" title="Editar">
                                        <i class="bi bi-pencil"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger" onclick="gestionMesas.eliminarMesa(${mesa.id}, '${mesa.numero}')" title="Eliminar">
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

    mostrarIndicadorMesa(mesaId, mesaNumero) {
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
                            <strong class="fs-5">Mesa ${mesaNumero} Activa</strong>
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

    seleccionarMesa(mesaId, mesaNumero) {
        // Cerrar modal de mesas
        const modalMesas = bootstrap.Modal.getInstance(document.getElementById('modalMesas'));
        if (modalMesas) {
            modalMesas.hide();
        }

        this.mesaSeleccionada = mesaId;
        localStorage.setItem('mesa_activa', mesaId);
        this.mostrarIndicadorMesa(mesaId, mesaNumero);
        this.mostrarNotificacion(`Mesa ${mesaNumero} seleccionada. Los productos se agregarán a esta mesa.`, 'success');
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
        if (!confirm('¿Desea cerrar esta mesa y generar la factura?')) {
            return;
        }

        // Obtener datos de la mesa
        try {
            const response = await fetch(`/pos/api/mesa/${mesaId}/items/`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Datos de la mesa:', data);

            if (data.success) {
                // Guardar el ID de la mesa para usarlo después
                this.mesaParaCerrar = mesaId;
                
                // Cargar items en el carrito
                this.cargarItemsEnCarrito(data.items);
                
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
                    alert('Error: El sistema de carrito no está disponible');
                }
            } else {
                alert('Error: ' + (data.error || 'No se pudieron cargar los items'));
            }
        } catch (error) {
            console.error('Error completo:', error);
            alert('Error al cargar los datos de la mesa: ' + error.message);
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
                
                // Redirigir a detalle de venta
                setTimeout(() => {
                    if (confirm('¿Desea ver la factura?')) {
                        window.location.href = `/pos/venta/${data.venta_id}/`;
                    }
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
                
                // Redirigir a detalle de venta
                setTimeout(() => {
                    if (confirm('¿Desea ver la factura?')) {
                        window.location.href = `/pos/venta/${data.venta_id}/`;
                    }
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
                            <form id="formCrearMesa">
                                <div class="mb-3">
                                    <label for="numero-mesa" class="form-label">Número de Mesa *</label>
                                    <input type="text" class="form-control" id="numero-mesa" required placeholder="Ej: 1, A1, VIP1">
                                </div>
                                <div class="mb-3">
                                    <label for="nombre-mesa" class="form-label">Nombre</label>
                                    <input type="text" class="form-control" id="nombre-mesa" placeholder="Ej: Mesa Principal">
                                </div>
                                <div class="mb-3">
                                    <label for="capacidad-mesa" class="form-label">Capacidad (personas)</label>
                                    <input type="number" class="form-control" id="capacidad-mesa" value="4" min="1" max="20">
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
        const numero = document.getElementById('numero-mesa').value.trim();
        const nombre = document.getElementById('nombre-mesa').value.trim() || `Mesa ${numero}`;
        const capacidad = parseInt(document.getElementById('capacidad-mesa').value);

        if (!numero) {
            alert('El número de mesa es obligatorio');
            return;
        }

        try {
            const response = await fetch('/pos/api/mesa/crear/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.obtenerCSRFToken()
                },
                body: JSON.stringify({ numero, nombre, capacidad })
            });

            const data = await response.json();

            if (data.success) {
                alert(data.mensaje);
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

    editarMesa(mesaId, numero, nombre, capacidad) {
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
                            <form id="formEditarMesa">
                                <div class="mb-3">
                                    <label for="edit-numero-mesa" class="form-label">Número de Mesa *</label>
                                    <input type="text" class="form-control" id="edit-numero-mesa" value="${numero}" required>
                                </div>
                                <div class="mb-3">
                                    <label for="edit-nombre-mesa" class="form-label">Nombre</label>
                                    <input type="text" class="form-control" id="edit-nombre-mesa" value="${nombre}">
                                </div>
                                <div class="mb-3">
                                    <label for="edit-capacidad-mesa" class="form-label">Capacidad (personas)</label>
                                    <input type="number" class="form-control" id="edit-capacidad-mesa" value="${capacidad}" min="1" max="20">
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
        const numero = document.getElementById('edit-numero-mesa').value.trim();
        const nombre = document.getElementById('edit-nombre-mesa').value.trim();
        const capacidad = parseInt(document.getElementById('edit-capacidad-mesa').value);

        try {
            const response = await fetch(`/pos/api/mesa/${mesaId}/editar/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.obtenerCSRFToken()
                },
                body: JSON.stringify({ numero, nombre, capacidad })
            });

            const data = await response.json();

            if (data.success) {
                alert(data.mensaje);
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

    async eliminarMesa(mesaId, numero) {
        if (!confirm(`¿Está seguro de eliminar la Mesa ${numero}?`)) {
            return;
        }

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
                alert(data.mensaje);
                this.cargarMesas();
            } else {
                alert('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al eliminar la mesa');
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
