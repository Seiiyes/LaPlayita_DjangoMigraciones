/**
 * Sistema de Carrito de Compras para el POS
 * Gestiona la lógica del carrito, búsqueda de productos y cálculos
 */

class CarritoPOS {
    constructor() {
        this.carrito = [];
        this.impuesto = 0.19; // 19%
        this.inicializar();
    }

    inicializar() {
        this.cargarCarritoDelLocalStorage();
        this.configurarEventos();
        this.actualizarVistaCarrito();
        this.actualizarTodosLosStocksVisuales(); // Actualizar stocks al cargar
    }

    configurarEventos() {
        // Búsqueda de productos
        const botonBusqueda = document.getElementById('product-search-button');
        const inputBusqueda = document.getElementById('product-search-input');

        if (botonBusqueda) {
            botonBusqueda.addEventListener('click', () => this.buscarProductos());
        }

        if (inputBusqueda) {
            inputBusqueda.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.buscarProductos();
                }
            });
        }

        // Botón de procesar venta
        const botonProcesar = document.querySelector('button.btn-success');
        if (botonProcesar && botonProcesar.textContent.includes('Procesar')) {
            botonProcesar.addEventListener('click', () => this.mostrarFormularioPago());
        }

        // Botón de cancelar venta
        const botonCancelar = document.querySelector('button.btn-outline-danger');
        if (botonCancelar && botonCancelar.textContent.includes('Cancelar')) {
            botonCancelar.addEventListener('click', () => this.vaciarCarrito());
        }
    }

    async buscarProductos() {
        const inputBusqueda = document.getElementById('product-search-input');
        const query = inputBusqueda.value.trim();

        if (!query) {
            this.cargarTodosLosProductos();
            return;
        }

        try {
            const response = await fetch(`/pos/api/buscar-productos/?q=${encodeURIComponent(query)}`);
            const datos = await response.json();

            if (datos.productos) {
                this.mostrarProductos(datos.productos);
            }
        } catch (error) {
            console.error('Error al buscar productos:', error);
            alert('Error al buscar productos');
        }
    }

    async cargarTodosLosProductos() {
        try {
            const inputBusqueda = document.getElementById('product-search-input');
            inputBusqueda.value = '';

            // Volver a la vista de categorías
            window.location.href = window.location.pathname;
        } catch (error) {
            console.error('Error al cargar productos:', error);
        }
    }

    mostrarProductos(productos) {
        const contenedorProductos = document.getElementById('product-list');
        contenedorProductos.innerHTML = '';

        if (productos.length === 0) {
            contenedorProductos.innerHTML = '<p class="col-12 text-center text-muted">No se encontraron productos</p>';
            return;
        }

        productos.forEach(producto => {
            const colDiv = document.createElement('div');
            colDiv.className = 'col';

            const cartaHTML = `
                <div class="card h-100 product-card">
                    <div class="card-body">
                        <h5 class="card-title">${this.escaparHTML(producto.nombre)}</h5>
                        <p class="card-text text-muted">${this.escaparHTML(producto.categoria)}</p>
                        ${producto.descripcion ? `<p class="card-text small">${this.escaparHTML(producto.descripcion)}</p>` : ''}
                        <p class="card-text fw-bold">$${this.formatearMoneda(producto.precio)}</p>
                        <p class="card-text small">
                            <span class="badge bg-info">Stock: ${producto.stock}</span>
                        </p>
                        <button class="btn btn-sm btn-primary agregar-producto-btn" data-producto-id="${producto.id}" data-nombre="${this.escaparHTML(producto.nombre)}" data-precio="${producto.precio}">
                            <i class="bi bi-plus-circle me-1"></i>Agregar
                        </button>
                    </div>
                </div>
            `;

            colDiv.innerHTML = cartaHTML;
            contenedorProductos.appendChild(colDiv);

            // Agregar evento al botón de agregar
            const btnAgregar = colDiv.querySelector('.agregar-producto-btn');
            btnAgregar.addEventListener('click', () => this.abrirModalProducto(producto.id));
        });
    }

    async abrirModalProducto(productoId) {
        try {
            const response = await fetch(`/pos/api/producto/${productoId}/`);
            const producto = await response.json();

            // Si hay un error al obtener el producto, mostrar notificación y salir.
            if (producto.error) {
                this.mostrarNotificacion('Error: ' + producto.error, 'danger');
                return;
            }

            // Validar si hay lotes disponibles.
            if (!producto.lotes || producto.lotes.length === 0) {
                this.mostrarNotificacion(`El producto "${this.escaparHTML(producto.nombre)}" no tiene lotes disponibles.`, 'warning');
                return;
            }

            // Filtrar lotes con stock disponible
            const lotesDisponibles = producto.lotes.filter(lote => lote.cantidad > 0);

            if (lotesDisponibles.length === 0) {
                this.mostrarNotificacion(`No hay stock disponible para "${this.escaparHTML(producto.nombre)}".`, 'danger');
                return;
            }

            // Mostrar modal para seleccionar lote y cantidad
            this.mostrarModalSeleccionLote(producto, lotesDisponibles);

        } catch (error) {
            console.error('Error al obtener producto:', error);
            this.mostrarNotificacion('Error al obtener detalles del producto.', 'danger');
        }
    }

    mostrarModalSeleccionLote(producto, lotes) {
        // Calcular stock total disponible
        const stockTotal = lotes.reduce((sum, lote) => sum + lote.cantidad, 0);

        const modalHTML = `
            <div class="modal fade" id="modalSeleccionLote" tabindex="-1">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title">
                                <i class="bi bi-cart-plus me-2"></i>${this.escaparHTML(producto.nombre)}
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="text-center mb-4">
                                <div class="display-6 text-primary mb-2">$${this.formatearMoneda(producto.precio)}</div>
                                <p class="text-muted mb-0">
                                    <i class="bi bi-box-seam me-1"></i>
                                    Disponible: <strong>${stockTotal}</strong> unidades
                                </p>
                            </div>
                            
                            <div class="mb-4">
                                <label for="input-cantidad" class="form-label fw-bold text-center d-block mb-3">
                                    ¿Cuántas unidades deseas agregar?
                                </label>
                                <div class="d-flex gap-2 mb-3">
                                    <button class="btn btn-outline-primary flex-fill" type="button" id="btn-cantidad-1">
                                        1
                                    </button>
                                    <button class="btn btn-outline-primary flex-fill" type="button" id="btn-cantidad-5">
                                        5
                                    </button>
                                    <button class="btn btn-outline-primary flex-fill" type="button" id="btn-cantidad-10">
                                        10
                                    </button>
                                    <button class="btn btn-outline-success flex-fill" type="button" id="btn-cantidad-max">
                                        <i class="bi bi-infinity"></i> Todo
                                    </button>
                                </div>
                                <div class="input-group input-group-lg">
                                    <button class="btn btn-outline-secondary" type="button" id="btn-decrementar">
                                        <i class="bi bi-dash-lg"></i>
                                    </button>
                                    <input type="number" id="input-cantidad" class="form-control text-center fw-bold fs-3" 
                                           value="1" min="1" max="${stockTotal}">
                                    <button class="btn btn-outline-secondary" type="button" id="btn-incrementar">
                                        <i class="bi bi-plus-lg"></i>
                                    </button>
                                </div>
                            </div>
                            
                            <div class="alert alert-success mb-0">
                                <div class="d-flex justify-content-between align-items-center">
                                    <span class="fw-bold">Subtotal:</span>
                                    <span class="fs-3 fw-bold">$<span id="subtotal-modal">${this.formatearMoneda(producto.precio)}</span></span>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                Cancelar
                            </button>
                            <button type="button" class="btn btn-success btn-lg px-5" id="btn-agregar-carrito">
                                <i class="bi bi-cart-plus me-2"></i>Agregar
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remover modal anterior si existe
        const modalAnterior = document.getElementById('modalSeleccionLote');
        if (modalAnterior) {
            modalAnterior.remove();
        }

        // Insertar nuevo modal
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Referencias a elementos
        const inputCantidad = document.getElementById('input-cantidad');
        const subtotalModal = document.getElementById('subtotal-modal');
        const btnIncrementar = document.getElementById('btn-incrementar');
        const btnDecrementar = document.getElementById('btn-decrementar');
        const btnAgregar = document.getElementById('btn-agregar-carrito');
        const btnCantidad1 = document.getElementById('btn-cantidad-1');
        const btnCantidad5 = document.getElementById('btn-cantidad-5');
        const btnCantidad10 = document.getElementById('btn-cantidad-10');
        const btnCantidadMax = document.getElementById('btn-cantidad-max');

        const actualizarSubtotal = () => {
            const cantidad = parseInt(inputCantidad.value) || 1;
            const subtotal = producto.precio * cantidad;
            subtotalModal.textContent = this.formatearMoneda(subtotal);
        };

        const setCantidad = (valor) => {
            const max = parseInt(inputCantidad.max);
            const min = parseInt(inputCantidad.min);
            let nuevaCantidad = parseInt(valor);
            
            if (nuevaCantidad > max) nuevaCantidad = max;
            if (nuevaCantidad < min) nuevaCantidad = min;
            
            inputCantidad.value = nuevaCantidad;
            actualizarSubtotal();
        };

        // Eventos botones rápidos
        btnCantidad1.addEventListener('click', () => setCantidad(1));
        btnCantidad5.addEventListener('click', () => setCantidad(5));
        btnCantidad10.addEventListener('click', () => setCantidad(10));
        btnCantidadMax.addEventListener('click', () => setCantidad(stockTotal));

        // Eventos
        inputCantidad.addEventListener('input', () => {
            const max = parseInt(inputCantidad.max);
            const min = parseInt(inputCantidad.min);
            let valor = parseInt(inputCantidad.value);
            
            if (valor > max) inputCantidad.value = max;
            if (valor < min) inputCantidad.value = min;
            
            actualizarSubtotal();
        });

        btnIncrementar.addEventListener('click', () => {
            const max = parseInt(inputCantidad.max);
            const actual = parseInt(inputCantidad.value);
            if (actual < max) {
                inputCantidad.value = actual + 1;
                actualizarSubtotal();
            }
        });

        btnDecrementar.addEventListener('click', () => {
            const min = parseInt(inputCantidad.min);
            const actual = parseInt(inputCantidad.value);
            if (actual > min) {
                inputCantidad.value = actual - 1;
                actualizarSubtotal();
            }
        });

        btnAgregar.addEventListener('click', () => {
            const cantidadTotal = parseInt(inputCantidad.value);
            
            // Distribuir la cantidad entre los lotes disponibles (FIFO)
            this.agregarProductoMultiLote(producto, lotes, cantidadTotal);
            
            // Cerrar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalSeleccionLote'));
            modal.hide();
        });

        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('modalSeleccionLote'));
        modal.show();
    }

    /**
     * Agrega un producto al carrito distribuyendo la cantidad entre múltiples lotes (FIFO)
     */
    agregarProductoMultiLote(producto, lotes, cantidadTotal) {
        // SIEMPRE agregar al carrito primero (tanto para mesa como para venta normal)
        let cantidadRestante = cantidadTotal;
        let lotesUsados = 0;

        // Ordenar lotes por fecha de caducidad (FIFO - primero los que vencen antes)
        const lotesOrdenados = [...lotes].sort((a, b) => {
            if (a.fecha_caducidad === 'N/A') return 1;
            if (b.fecha_caducidad === 'N/A') return -1;
            return new Date(a.fecha_caducidad) - new Date(b.fecha_caducidad);
        });

        // Distribuir la cantidad entre los lotes
        for (const lote of lotesOrdenados) {
            if (cantidadRestante <= 0) break;

            const cantidadDeLote = Math.min(cantidadRestante, lote.cantidad);
            
            this.agregarAlCarrito(
                producto.id,
                producto.nombre,
                producto.precio,
                cantidadDeLote,
                lote.id,
                lote.cantidad
            );

            cantidadRestante -= cantidadDeLote;
            lotesUsados++;
        }

        // Mostrar notificación informativa
        const mesaActiva = window.gestionMesas && window.gestionMesas.mesaSeleccionada;
        if (lotesUsados > 1) {
            this.mostrarNotificacion(
                `${producto.nombre}: ${cantidadTotal} unidades agregadas ${mesaActiva ? 'al carrito' : 'usando ' + lotesUsados + ' lotes'}`,
                'success'
            );
        } else if (mesaActiva) {
            this.mostrarNotificacion(
                `${producto.nombre} agregado al carrito. Click "Agregar a Mesa" para confirmar.`,
                'info'
            );
        }
    }

    /**
     * Agrega todo el carrito a la mesa con anotación
     */
    async agregarCarritoAMesa(mesaId) {
        if (this.carrito.length === 0) {
            alert('El carrito está vacío');
            return;
        }

        // Mostrar modal con productos y anotaciones
        this.mostrarModalAnotaciones(mesaId);
    }

    mostrarModalAnotaciones(mesaId) {
        // Crear HTML de productos con campos de anotación
        let productosHTML = '';
        this.carrito.forEach((item, index) => {
            productosHTML += `
                <div class="producto-anotacion mb-3 p-3 border rounded">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <h6 class="mb-1"><strong>${this.escaparHTML(item.nombre)}</strong></h6>
                            <small class="text-muted">Cantidad: ${item.cantidad} | Precio: $${this.formatearMoneda(item.precio)}</small>
                        </div>
                        <span class="badge bg-primary">$${this.formatearMoneda(item.precio * item.cantidad)}</span>
                    </div>
                    <div class="input-group">
                        <span class="input-group-text"><i class="bi bi-chat-left-text"></i></span>
                        <input type="text" class="form-control anotacion-input" data-index="${index}" 
                               placeholder="Ej: Sin cebolla, Extra picante, Para llevar..." 
                               maxlength="200">
                    </div>
                </div>
            `;
        });

        const modalHTML = `
            <div class="modal fade" id="modalAnotaciones" tabindex="-1">
                <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
                    <div class="modal-content">
                        <div class="modal-header bg-success text-white">
                            <h5 class="modal-title">
                                <i class="bi bi-cart-check me-2"></i>Confirmar Pedido para Mesa
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-info mb-3">
                                <i class="bi bi-info-circle me-2"></i>
                                <strong>Revisa los productos y agrega anotaciones si es necesario</strong>
                                <br>
                                <small>Las anotaciones son opcionales y ayudan a especificar preferencias del cliente</small>
                            </div>
                            <div id="productos-anotaciones">
                                ${productosHTML}
                            </div>
                            <div class="alert alert-success mt-3 mb-0">
                                <div class="d-flex justify-content-between align-items-center">
                                    <strong class="fs-5">Total del Pedido:</strong>
                                    <span class="fs-4">$${this.formatearMoneda(this.carrito.reduce((sum, item) => sum + (item.precio * item.cantidad), 0))}</span>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="bi bi-x-circle me-1"></i>Cancelar
                            </button>
                            <button type="button" class="btn btn-success btn-lg" id="btn-confirmar-agregar-mesa">
                                <i class="bi bi-check-circle-fill me-1"></i>Confirmar y Agregar a Mesa
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remover modal anterior si existe
        const modalAnterior = document.getElementById('modalAnotaciones');
        if (modalAnterior) {
            modalAnterior.remove();
        }

        // Insertar nuevo modal
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Evento para confirmar
        document.getElementById('btn-confirmar-agregar-mesa').addEventListener('click', () => {
            this.confirmarAgregarAMesa(mesaId);
        });

        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('modalAnotaciones'));
        modal.show();
    }

    async confirmarAgregarAMesa(mesaId) {
        // Recopilar anotaciones
        const inputs = document.querySelectorAll('.anotacion-input');
        const items = this.carrito.map((item, index) => ({
            producto_id: item.producto_id,
            lote_id: item.lote_id,
            cantidad: item.cantidad,
            anotacion: inputs[index].value.trim()
        }));

        // Deshabilitar botón
        const btnConfirmar = document.getElementById('btn-confirmar-agregar-mesa');
        const textoOriginal = btnConfirmar.innerHTML;
        btnConfirmar.disabled = true;
        btnConfirmar.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Agregando...';

        try {
            const response = await fetch(`/pos/api/mesa/${mesaId}/agregar-item/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.obtenerCSRFToken()
                },
                body: JSON.stringify({ items })
            });

            const data = await response.json();

            if (data.success) {
                // Cerrar modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalAnotaciones'));
                modal.hide();

                this.mostrarNotificacion(
                    `${items.length} producto(s) agregado(s) a la mesa. Total: $${data.total_cuenta.toFixed(2)}`,
                    'success'
                );
                
                // Vaciar carrito
                this.vaciarCarrito();
            } else {
                this.mostrarNotificacion('Error: ' + data.error, 'danger');
                btnConfirmar.disabled = false;
                btnConfirmar.innerHTML = textoOriginal;
            }
        } catch (error) {
            console.error('Error:', error);
            this.mostrarNotificacion('Error al agregar productos a la mesa', 'danger');
            btnConfirmar.disabled = false;
            btnConfirmar.innerHTML = textoOriginal;
        }
    }

    /**
     * Agrega productos directamente a una mesa
     */
    async agregarProductoAMesa(producto, lotes, cantidadTotal, mesaId) {
        // Ordenar lotes por fecha de caducidad (FIFO)
        const lotesOrdenados = [...lotes].sort((a, b) => {
            if (a.fecha_caducidad === 'N/A') return 1;
            if (b.fecha_caducidad === 'N/A') return -1;
            return new Date(a.fecha_caducidad) - new Date(b.fecha_caducidad);
        });

        // Preparar items para enviar
        const items = [];
        let cantidadRestante = cantidadTotal;

        for (const lote of lotesOrdenados) {
            if (cantidadRestante <= 0) break;

            const cantidadDeLote = Math.min(cantidadRestante, lote.cantidad);
            
            items.push({
                producto_id: producto.id,
                lote_id: lote.id,
                cantidad: cantidadDeLote
            });

            cantidadRestante -= cantidadDeLote;
        }

        // Enviar a la API de la mesa
        try {
            const response = await fetch(`/pos/api/mesa/${mesaId}/agregar-item/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.obtenerCSRFToken()
                },
                body: JSON.stringify({ items })
            });

            const data = await response.json();

            if (data.success) {
                this.mostrarNotificacion(
                    `${producto.nombre} (${cantidadTotal} unidades) agregado a la mesa. Total: $${data.total_cuenta.toFixed(2)}`,
                    'success'
                );
            } else {
                this.mostrarNotificacion('Error: ' + data.error, 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            this.mostrarNotificacion('Error al agregar producto a la mesa', 'danger');
        }
    }

    agregarAlCarrito(productoId, nombre, precio, cantidad, loteId, maxStock) {
        // Verificar si el producto ya está en el carrito con el mismo lote
        const itemExistente = this.carrito.find(item => item.producto_id === productoId && item.lote_id === loteId);

        if (itemExistente) {
            // Actualizar el stock máximo con la información más reciente
            itemExistente.max_stock = maxStock;

            if (itemExistente.cantidad + cantidad > itemExistente.max_stock) {
                this.mostrarNotificacion(`No puedes agregar más. Stock máximo disponible: ${itemExistente.max_stock}`, 'warning');
                return;
            }
            itemExistente.cantidad += cantidad;
        } else {
            if (cantidad > maxStock) {
                this.mostrarNotificacion(`Stock insuficiente. Disponible: ${maxStock}`, 'warning');
                return;
            }
            this.carrito.push({
                producto_id: productoId,
                nombre: nombre,
                precio: parseFloat(precio),
                cantidad: cantidad,
                lote_id: loteId,
                max_stock: maxStock
            });
        }

        this.guardarCarritoEnLocalStorage();
        this.actualizarVistaCarrito();
        this.actualizarStockVisual(productoId); // Actualizar stock visual
        this.mostrarNotificacion(`${nombre} agregado al carrito`);
    }

    removerDelCarrito(index) {
        const item = this.carrito[index];
        const productoId = item.producto_id;
        
        this.carrito.splice(index, 1);
        this.guardarCarritoEnLocalStorage();
        this.actualizarVistaCarrito();
        this.actualizarStockVisual(productoId); // Actualizar stock visual
    }

    actualizarCantidadCarrito(index, nuevaCantidad) {
        nuevaCantidad = parseInt(nuevaCantidad);
        const item = this.carrito[index];
        const productoId = item.producto_id;

        if (nuevaCantidad <= 0) {
            this.removerDelCarrito(index);
            return;
        }

        if (item.max_stock && nuevaCantidad > item.max_stock) {
            this.mostrarNotificacion(`Solo hay ${item.max_stock} unidades disponibles de este lote.`, 'warning');
            nuevaCantidad = item.max_stock;
            // Forzar actualización visual del input si el usuario escribió un número mayor
            const input = document.querySelector(`input[data-index="${index}"]`);
            if (input) input.value = nuevaCantidad;
        }

        this.carrito[index].cantidad = nuevaCantidad;
        this.guardarCarritoEnLocalStorage();
        this.actualizarVistaCarrito();
        this.actualizarStockVisual(productoId); // Actualizar stock visual
    }

    actualizarVistaCarrito() {
        const contenedorItems = document.getElementById('cart-items');
        const subtotalSpan = document.getElementById('cart-subtotal');
        const impuestoSpan = document.getElementById('cart-tax');
        const totalSpan = document.getElementById('cart-total');

        contenedorItems.innerHTML = '';

        if (this.carrito.length === 0) {
            contenedorItems.innerHTML = '<tr><td colspan="4" class="text-center text-muted">El carrito está vacío</td></tr>';
            subtotalSpan.textContent = '$0.00';
            impuestoSpan.textContent = '$0.00';
            totalSpan.textContent = '$0.00';
            return;
        }

        let subtotal = 0;

        this.carrito.forEach((item, index) => {
            const subtotalItem = item.precio * item.cantidad;
            subtotal += subtotalItem;

            const fila = document.createElement('tr');
            fila.innerHTML = `
                <td>
                    <div>
                        <strong>${this.escaparHTML(item.nombre)}</strong>
                        <br>
                        <small class="text-muted">Lote ID: ${item.lote_id}</small>
                    </div>
                </td>
                <td class="text-end">
                    <input type="number" class="form-control form-control-sm" style="width: 70px;" value="${item.cantidad}" min="1" data-index="${index}">
                </td>
                <td class="text-end">
                    $${this.formatearMoneda(item.precio)} x ${item.cantidad} = <br>
                    <strong>$${this.formatearMoneda(subtotalItem)}</strong>
                </td>
                <td class="text-center">
                    <button class="btn btn-sm btn-outline-danger eliminar-btn" data-index="${index}" title="Eliminar">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;

            contenedorItems.appendChild(fila);

            // Eventos
            const inputCantidad = fila.querySelector('input[type="number"]');
            inputCantidad.addEventListener('change', (e) => {
                this.actualizarCantidadCarrito(index, e.target.value);
            });

            const btnEliminar = fila.querySelector('.eliminar-btn');
            btnEliminar.addEventListener('click', () => {
                this.removerDelCarrito(index);
            });
        });

        // Calcular impuesto (solo informativo, no se suma al total)
        const impuesto = subtotal * this.impuesto;
        const total = subtotal; // Total = Subtotal (impuesto incluido en precio)

        subtotalSpan.textContent = `$${this.formatearMoneda(subtotal)}`;
        impuestoSpan.textContent = `$${this.formatearMoneda(impuesto)}`;
        totalSpan.textContent = `$${this.formatearMoneda(total)}`;
    }

    async mostrarFormularioPago() {
        if (this.carrito.length === 0) {
            alert('El carrito está vacío');
            return;
        }

        // Obtener el cliente seleccionado del selector principal
        const clienteSelectPrincipal = document.getElementById('cliente-select');
        const clienteSeleccionado = clienteSelectPrincipal ? clienteSelectPrincipal.value : '';
        
        console.log('Cliente seleccionado en el selector principal:', clienteSeleccionado);

        // Obtener clientes desde la API
        let clientesHTML = '<option value="">Consumidor Final</option>';

        try {
            console.log('Obteniendo clientes...');
            const response = await fetch('/pos/api/obtener-clientes/');
            console.log('Response status:', response.status);

            if (response.ok) {
                const data = await response.json();
                console.log('Datos recibidos:', data);

                if (data.success && data.clientes && data.clientes.length > 0) {
                    // Construir opciones de clientes
                    data.clientes.forEach(cliente => {
                        const selected = clienteSeleccionado && cliente.id == clienteSeleccionado ? 'selected' : '';
                        clientesHTML += `<option value="${cliente.id}" ${selected}>${this.escaparHTML(cliente.nombre)}</option>`;
                    });
                    console.log(`Se cargaron ${data.clientes.length} clientes`);
                }
            } else {
                console.error('Error en respuesta:', response.statusText);
            }
        } catch (error) {
            console.error('Error al obtener clientes:', error);
        }

        // Crear el modal con los clientes obtenidos
        const formularioHTML = `
            <div class="modal fade" id="modalPago" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Completar Venta</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="form-pago">
                                <div class="mb-3">
                                    <label for="cliente-pago" class="form-label">Cliente (Opcional):</label>
                                    <select id="cliente-pago" class="form-control">
                                        ${clientesHTML}
                                    </select>
                                </div>

                                <div class="mb-3">
                                    <label for="metodo-pago" class="form-label">Método de Pago:</label>
                                    <select id="metodo-pago" class="form-control" required>
                                        <option value="">-- Seleccione --</option>
                                        <option value="efectivo">Efectivo</option>
                                        <option value="tarjeta_debito">Tarjeta Débito</option>
                                        <option value="tarjeta_credito">Tarjeta Crédito</option>
                                        <option value="transferencia">Transferencia</option>
                                        <option value="cheque">Cheque</option>
                                    </select>
                                </div>

                                <div class="mb-3">
                                    <label for="canal-venta" class="form-label">Canal de Venta:</label>
                                    <select id="canal-venta" class="form-control" required>
                                        <option value="">-- Seleccione --</option>
                                        <option value="mostrador">Mostrador</option>
                                        <option value="telefono">Teléfono</option>
                                        <option value="online">Online</option>
                                        <option value="delivery">Delivery</option>
                                    </select>
                                </div>

                                <div class="alert alert-info">
                                    <p><strong>Subtotal:</strong> $<span id="modal-subtotal">0.00</span></p>
                                    <p><strong>Impuestos (19%):</strong> $<span id="modal-impuesto">0.00</span></p>
                                    <p class="fs-5"><strong>Total a Pagar:</strong> $<span id="modal-total">0.00</span></p>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-success" id="btn-confirmar-venta">
                                <i class="bi bi-check-circle me-1"></i>Confirmar Venta
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remover modal anterior si existe
        const modalAnterior = document.getElementById('modalPago');
        if (modalAnterior) {
            modalAnterior.remove();
        }

        // Insertar nuevo modal
        document.body.insertAdjacentHTML('beforeend', formularioHTML);

        // Calcular y mostrar totales
        let subtotal = 0;
        this.carrito.forEach(item => {
            subtotal += item.precio * item.cantidad;
        });
        const impuesto = subtotal * this.impuesto;
        const total = subtotal; // Total = Subtotal (impuesto incluido en precio)

        document.getElementById('modal-subtotal').textContent = this.formatearMoneda(subtotal);
        document.getElementById('modal-impuesto').textContent = this.formatearMoneda(impuesto);
        document.getElementById('modal-total').textContent = this.formatearMoneda(total);

        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('modalPago'));

        // Agregar evento al botón de confirmar
        document.getElementById('btn-confirmar-venta').addEventListener('click', () => {
            this.confirmarVenta();
            modal.hide();
        });

        modal.show();
    }

    async confirmarVenta() {
        const clienteIdSeleccionado = document.getElementById('cliente-pago').value;
        // Si no se selecciona cliente, usar Consumidor Final (ID 1)
        const clienteId = clienteIdSeleccionado ? parseInt(clienteIdSeleccionado) : 1;
        const metodoPago = document.getElementById('metodo-pago').value;
        const canalVenta = document.getElementById('canal-venta').value;

        console.log('Cliente ID para la venta:', clienteId);

        // Validar que los campos requeridos estén completos
        if (!metodoPago || metodoPago.trim() === '') {
            alert('Por favor seleccione un Método de Pago');
            return;
        }
        if (!canalVenta || canalVenta.trim() === '') {
            alert('Por favor seleccione un Canal de Venta');
            return;
        }

        // Mostrar indicador de carga
        const btnConfirmar = document.getElementById('btn-confirmar-venta');
        const textoOriginal = btnConfirmar.innerHTML;
        btnConfirmar.disabled = true;
        btnConfirmar.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Procesando...';

        try {
            const response = await fetch('/pos/api/procesar-venta/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.obtenerCSRFToken(),
                },
                body: JSON.stringify({
                    cliente_id: clienteId,
                    metodo_pago: metodoPago,
                    canal_venta: canalVenta,
                    items: this.carrito
                })
            });

            const datos = await response.json();

            if (response.ok && datos.success) {
                let mensaje = datos.mensaje;
                if (datos.puntos_ganados && datos.puntos_ganados > 0) {
                    mensaje += ` ¡Has ganado ${datos.puntos_ganados.toFixed(2)} puntos!`;
                }
                this.mostrarNotificacion(mensaje, 'success');
                this.vaciarCarrito();
                this.redirigirAVentaDetalle(datos.venta_id);
            } else {
                alert('Error: ' + (datos.error || 'Error desconocido'));
            }
        } catch (error) {
            console.error('Error al procesar venta:', error);
            alert('Error al procesar la venta');
        } finally {
            btnConfirmar.disabled = false;
            btnConfirmar.innerHTML = textoOriginal;
        }
    }

    redirigirAVentaDetalle(ventaId) {
        setTimeout(() => {
            window.location.href = `/pos/venta/${ventaId}/`;
        }, 1500);
    }

    vaciarCarrito() {
        // Guardar IDs de productos antes de vaciar
        const productosIds = [...new Set(this.carrito.map(item => item.producto_id))];
        
        this.carrito = [];
        this.guardarCarritoEnLocalStorage();
        this.actualizarVistaCarrito();
        
        // Actualizar stock visual de todos los productos que estaban en el carrito
        productosIds.forEach(productoId => this.actualizarStockVisual(productoId));
    }

    /**
     * Actualiza todos los stocks visuales de productos que están en el carrito
     */
    actualizarTodosLosStocksVisuales() {
        // Obtener IDs únicos de productos en el carrito
        const productosIds = [...new Set(this.carrito.map(item => item.producto_id))];
        
        // Actualizar cada uno
        productosIds.forEach(productoId => this.actualizarStockVisual(productoId));
    }

    /**
     * Actualiza el stock visual mostrado en la tarjeta del producto
     * Calcula: Stock Real - Cantidad en Carrito = Stock Disponible
     */
    actualizarStockVisual(productoId) {
        // Buscar todos los items del producto en el carrito (puede haber múltiples lotes)
        const itemsEnCarrito = this.carrito.filter(item => item.producto_id === productoId);
        
        // Calcular cantidad total en carrito para este producto
        const cantidadEnCarrito = itemsEnCarrito.reduce((total, item) => total + item.cantidad, 0);
        
        // Buscar la tarjeta del producto en el DOM
        const btnProducto = document.querySelector(`button[data-producto-id="${productoId}"]`);
        if (!btnProducto) return;
        
        const tarjetaProducto = btnProducto.closest('.product-card');
        if (!tarjetaProducto) return;
        
        const badgeStock = tarjetaProducto.querySelector('.badge-stock');
        if (!badgeStock) return;
        
        // Obtener el stock real del atributo data o del texto actual
        let stockReal = parseInt(badgeStock.dataset.stockReal);
        
        // Si no existe el atributo, guardarlo la primera vez
        if (isNaN(stockReal)) {
            const textoStock = badgeStock.textContent.match(/\d+/);
            stockReal = textoStock ? parseInt(textoStock[0]) : 0;
            badgeStock.dataset.stockReal = stockReal;
        }
        
        // Calcular stock disponible
        const stockDisponible = stockReal - cantidadEnCarrito;
        
        // Actualizar el texto del badge
        if (cantidadEnCarrito > 0) {
            badgeStock.innerHTML = `Stock: ${stockDisponible} <small>(${cantidadEnCarrito} en carrito)</small>`;
            badgeStock.classList.remove('bg-info', 'bg-success');
            badgeStock.classList.add('bg-warning', 'text-dark');
        } else {
            badgeStock.textContent = `Stock: ${stockReal}`;
            badgeStock.classList.remove('bg-warning', 'text-dark');
            badgeStock.classList.add(stockReal <= 10 ? 'bg-warning text-dark' : 'bg-info');
        }
        
        // Deshabilitar botón si no hay stock disponible
        if (stockDisponible <= 0) {
            btnProducto.disabled = true;
            btnProducto.classList.add('disabled');
            btnProducto.innerHTML = '<i class="bi bi-x-circle"></i> Sin stock';
        } else {
            btnProducto.disabled = false;
            btnProducto.classList.remove('disabled');
            btnProducto.innerHTML = '<i class="bi bi-plus-circle"></i>';
        }
    }

    guardarCarritoEnLocalStorage() {
        localStorage.setItem('carrito_pos', JSON.stringify(this.carrito));
    }

    cargarCarritoDelLocalStorage() {
        const carritoGuardado = localStorage.getItem('carrito_pos');
        if (carritoGuardado) {
            try {
                this.carrito = JSON.parse(carritoGuardado);
            } catch (error) {
                this.carrito = [];
            }
        }
    }

    calcularSubtotal() {
        return this.carrito.reduce((sum, item) => sum + (item.precio * item.cantidad), 0);
    }

    calcularImpuestos() {
        return this.calcularSubtotal() * this.impuesto;
    }

    calcularTotal() {
        return this.calcularSubtotal(); // Total = Subtotal (impuesto incluido en precio)
    }

    mostrarFormularioPago() {
        if (this.carrito.length === 0) {
            this.mostrarNotificacion('El carrito está vacío', 'warning');
            return;
        }

        const subtotal = this.calcularSubtotal();
        const impuestos = this.calcularImpuestos();
        const total = this.calcularTotal();

        const itemsHTML = this.carrito.map(item => `
            <tr>
                <td>${this.escaparHTML(item.nombre)}</td>
                <td class="text-center">${item.cantidad}</td>
                <td class="text-end">$${this.formatearMoneda(item.precio)}</td>
                <td class="text-end">$${this.formatearMoneda(item.precio * item.cantidad)}</td>
            </tr>
        `).join('');

        const modalHTML = `
            <div class="modal fade" id="modalCompletarVenta" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-success text-white">
                            <h5 class="modal-title">
                                <i class="bi bi-check-circle me-2"></i>Completar Venta
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6 class="mb-3"><i class="bi bi-cart-check me-2"></i>Resumen del Carrito</h6>
                                    <div class="table-responsive" style="max-height: 300px; overflow-y: auto;">
                                        <table class="table table-sm">
                                            <thead>
                                                <tr>
                                                    <th>Producto</th>
                                                    <th class="text-center">Cant.</th>
                                                    <th class="text-end">Precio</th>
                                                    <th class="text-end">Subtotal</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${itemsHTML}
                                            </tbody>
                                            <tfoot>
                                                <tr>
                                                    <th colspan="3" class="text-end">Subtotal:</th>
                                                    <th class="text-end">$${this.formatearMoneda(subtotal)}</th>
                                                </tr>
                                                <tr>
                                                    <th colspan="3" class="text-end">Impuestos (19%):</th>
                                                    <th class="text-end">$${this.formatearMoneda(impuestos)}</th>
                                                </tr>
                                                <tr class="table-success">
                                                    <th colspan="3" class="text-end">TOTAL:</th>
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
                                            <label for="cliente-modal" class="form-label">
                                                <i class="bi bi-person me-1"></i>Cliente *
                                            </label>
                                            <select class="form-select" id="cliente-modal" required>
                                                <option value="">Cargando clientes...</option>
                                            </select>
                                        </div>
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
                                    </form>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="bi bi-x-circle me-1"></i>Cancelar
                            </button>
                            <button type="button" class="btn btn-success" onclick="carritoPOS.procesarVenta()">
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

        // Cargar clientes en el selector del modal
        this.cargarClientesEnModal();

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

    async cargarClientesEnModal() {
        const clienteModal = document.getElementById('cliente-modal');
        if (!clienteModal) return;

        // Obtener el cliente seleccionado del selector principal
        const clienteSelectPrincipal = document.getElementById('cliente-select');
        const clienteSeleccionado = clienteSelectPrincipal ? clienteSelectPrincipal.value : '1';

        try {
            const response = await fetch('/pos/api/obtener-clientes/');
            const data = await response.json();

            if (data.success && data.clientes) {
                clienteModal.innerHTML = '<option value="1">Consumidor Final</option>';
                
                data.clientes.forEach(cliente => {
                    const selected = cliente.id == clienteSeleccionado ? 'selected' : '';
                    clienteModal.innerHTML += `<option value="${cliente.id}" ${selected}>${this.escaparHTML(cliente.nombre)}</option>`;
                });
            } else {
                clienteModal.innerHTML = '<option value="1" selected>Consumidor Final</option>';
            }
        } catch (error) {
            console.error('Error al cargar clientes:', error);
            clienteModal.innerHTML = '<option value="1" selected>Consumidor Final</option>';
        }
    }

    async procesarVenta() {
        const metodoPago = document.getElementById('metodo-pago').value;
        const montoRecibido = parseFloat(document.getElementById('monto-recibido').value) || 0;
        const clienteId = document.getElementById('cliente-modal').value;

        if (!metodoPago) {
            this.mostrarNotificacion('Por favor seleccione un método de pago', 'warning');
            return;
        }

        if (!clienteId) {
            this.mostrarNotificacion('Por favor seleccione un cliente', 'warning');
            return;
        }

        // Preparar datos de la venta
        const ventaData = {
            cliente_id: clienteId,
            metodo_pago: metodoPago,
            canal_venta: 'mostrador',
            monto_recibido: montoRecibido,
            items: this.carrito.map(item => ({
                producto_id: item.producto_id,
                lote_id: item.lote_id,
                cantidad: item.cantidad,
                precio: item.precio
            }))
        };

        try {
            const response = await fetch('/pos/api/procesar-venta/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.obtenerCSRFToken()
                },
                body: JSON.stringify(ventaData)
            });

            const data = await response.json();

            if (data.success) {
                // Guardar el total ANTES de vaciar el carrito
                const totalVenta = data.total || this.calcularTotal();
                
                // Cerrar modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalCompletarVenta'));
                if (modal) modal.hide();

                this.vaciarCarrito();

                // Mostrar modal de éxito con opciones
                this.mostrarModalExitoVenta(data.venta_id, totalVenta);
            } else {
                this.mostrarNotificacion('Error: ' + data.error, 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            this.mostrarNotificacion('Error al procesar la venta', 'danger');
        }
    }

    mostrarModalExitoVenta(ventaId, total) {
        // Remover modal anterior si existe
        const modalAnterior = document.getElementById('modalExitoVenta');
        if (modalAnterior) modalAnterior.remove();

        const modalHTML = `
            <div class="modal fade" id="modalExitoVenta" tabindex="-1" data-bs-backdrop="static" data-bs-keyboard="false">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-0 shadow-lg" style="border-radius: 20px; overflow: hidden;">
                        <!-- Header con animación de éxito -->
                        <div class="modal-header border-0 text-white py-4" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
                            <div class="w-100 text-center">
                                <div class="mb-3">
                                    <div class="success-checkmark">
                                        <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52" style="width: 80px; height: 80px;">
                                            <circle class="checkmark__circle" cx="26" cy="26" r="25" fill="none" stroke="#fff" stroke-width="2"/>
                                            <path class="checkmark__check" fill="none" stroke="#fff" stroke-width="4" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                                        </svg>
                                    </div>
                                </div>
                                <h4 class="modal-title fw-bold mb-1">¡Venta Exitosa!</h4>
                                <p class="mb-0 opacity-75">Factura #${ventaId} generada correctamente</p>
                            </div>
                        </div>
                        
                        <!-- Body -->
                        <div class="modal-body text-center py-4">
                            <div class="mb-4">
                                <p class="text-muted mb-2">Total de la venta</p>
                                <h2 class="fw-bold text-success mb-0">$${this.formatearMoneda(total)}</h2>
                            </div>
                            
                            <p class="text-muted mb-0">
                                <i class="bi bi-question-circle me-1"></i>
                                ¿Qué deseas hacer ahora?
                            </p>
                        </div>
                        
                        <!-- Footer con botones -->
                        <div class="modal-footer border-0 justify-content-center gap-2 pb-4">
                            <button type="button" class="btn btn-outline-secondary btn-lg px-4" id="btn-nueva-venta" style="border-radius: 12px;">
                                <i class="bi bi-plus-circle me-2"></i>Nueva Venta
                            </button>
                            <button type="button" class="btn btn-success btn-lg px-4" id="btn-ver-factura" style="border-radius: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none;">
                                <i class="bi bi-receipt me-2"></i>Ver Factura
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <style>
                .success-checkmark {
                    animation: scaleIn 0.5s ease-in-out;
                }
                
                @keyframes scaleIn {
                    0% {
                        transform: scale(0);
                        opacity: 0;
                    }
                    50% {
                        transform: scale(1.2);
                    }
                    100% {
                        transform: scale(1);
                        opacity: 1;
                    }
                }
                
                .checkmark__circle {
                    stroke-dasharray: 166;
                    stroke-dashoffset: 166;
                    animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
                }
                
                .checkmark__check {
                    stroke-dasharray: 48;
                    stroke-dashoffset: 48;
                    animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.6s forwards;
                }
                
                @keyframes stroke {
                    100% {
                        stroke-dashoffset: 0;
                    }
                }
                
                #modalExitoVenta .btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }
                
                #modalExitoVenta .btn {
                    transition: all 0.3s ease;
                }
            </style>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);

        const modal = new bootstrap.Modal(document.getElementById('modalExitoVenta'));
        modal.show();

        // Evento para ver factura
        document.getElementById('btn-ver-factura').addEventListener('click', () => {
            window.location.href = `/pos/venta/${ventaId}/`;
        });

        // Evento para nueva venta
        document.getElementById('btn-nueva-venta').addEventListener('click', () => {
            modal.hide();
            // Recargar la página para una nueva venta limpia
            window.location.reload();
        });
    }

    mostrarNotificacion(mensaje, tipo = 'info') {
        const alertaHTML = `
            <div class="alert alert-${tipo} alert-dismissible fade show position-fixed" style="top: 20px; right: 20px; z-index: 9999;" role="alert">
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

    escaparHTML(texto) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return texto.replace(/[&<>"']/g, m => map[m]);
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

// Inicializar el carrito cuando el documento esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.carritoPOS = new CarritoPOS();
});
