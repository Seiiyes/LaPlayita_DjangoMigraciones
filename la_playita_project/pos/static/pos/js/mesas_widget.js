/**
 * Widget de Estado de Mesas para POS
 * Muestra un resumen compacto del estado de las mesas en el POS principal
 */

class MesasWidget {
    constructor() {
        this.mesasData = [];
        this.widgetCreado = false;
        this.inicializar();
    }

    inicializar() {
        this.crearWidget();
        this.cargarDatos();
        
        // Actualizar cada 15 segundos
        setInterval(() => {
            this.cargarDatos();
        }, 15000);
    }

    crearWidget() {
        if (this.widgetCreado) return;

        // Buscar un lugar apropiado para insertar el widget
        const contenedorCarrito = document.querySelector('.cart-section');
        if (!contenedorCarrito) return;

        const widgetHTML = `
            <div id="mesas-widget" class="card mb-3" style="border-radius: 12px; border: 2px solid #e9ecef;">
                <div class="card-header bg-light d-flex justify-content-between align-items-center py-2">
                    <h6 class="mb-0 fw-bold text-dark">
                        <i class="bi bi-grid-3x3-gap me-2 text-success"></i>Estado de Mesas
                    </h6>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-success btn-sm" onclick="mesasWidget.toggleWidget()" title="Minimizar/Expandir">
                            <i class="bi bi-chevron-up" id="widget-toggle-icon"></i>
                        </button>
                        <a href="/pos/mesas/" class="btn btn-success btn-sm" title="Dashboard completo">
                            <i class="bi bi-speedometer2"></i>
                        </a>
                    </div>
                </div>
                <div class="card-body p-3" id="mesas-widget-body">
                    <!-- Estadísticas rápidas -->
                    <div class="row text-center mb-3">
                        <div class="col-3">
                            <div class="text-success">
                                <i class="bi bi-check-circle-fill fs-4"></i>
                                <div class="fw-bold" id="widget-disponibles">0</div>
                                <small class="text-muted">Libres</small>
                            </div>
                        </div>
                        <div class="col-3">
                            <div class="text-danger">
                                <i class="bi bi-door-closed-fill fs-4"></i>
                                <div class="fw-bold" id="widget-ocupadas">0</div>
                                <small class="text-muted">Ocupadas</small>
                            </div>
                        </div>
                        <div class="col-3">
                            <div class="text-warning">
                                <i class="bi bi-clock-fill fs-4"></i>
                                <div class="fw-bold" id="widget-reservadas">0</div>
                                <small class="text-muted">Reserv.</small>
                            </div>
                        </div>
                        <div class="col-3">
                            <div class="text-info">
                                <i class="bi bi-currency-dollar fs-4"></i>
                                <div class="fw-bold" id="widget-total">$0</div>
                                <small class="text-muted">Total</small>
                            </div>
                        </div>
                    </div>

                    <!-- Lista de mesas ocupadas -->
                    <div id="mesas-ocupadas-lista">
                        <h6 class="text-muted mb-2 small">Mesas Ocupadas:</h6>
                        <div id="mesas-ocupadas-items" class="d-flex flex-wrap gap-1">
                            <!-- Items de mesas ocupadas -->
                        </div>
                    </div>

                    <!-- Acciones rápidas -->
                    <div class="mt-3 pt-2 border-top">
                        <div class="d-flex gap-2">
                            <button class="btn btn-sm btn-outline-primary flex-fill" onclick="mesasWidget.abrirModalMesas()">
                                <i class="bi bi-grid-3x3-gap me-1"></i>Gestionar
                            </button>
                            <button class="btn btn-sm btn-outline-success flex-fill" onclick="mesasWidget.crearMesaRapida()">
                                <i class="bi bi-plus-circle me-1"></i>Nueva
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Insertar el widget antes del carrito
        contenedorCarrito.insertAdjacentHTML('beforebegin', widgetHTML);
        this.widgetCreado = true;
    }

    async cargarDatos() {
        try {
            const response = await fetch('/pos/api/mesas/');
            const data = await response.json();

            if (data.success) {
                this.mesasData = data.mesas;
                this.actualizarWidget();
            }
        } catch (error) {
            console.error('Error al cargar datos de mesas:', error);
        }
    }

    actualizarWidget() {
        if (!this.widgetCreado) return;

        // Calcular estadísticas
        const disponibles = this.mesasData.filter(m => m.estado === 'disponible').length;
        const ocupadas = this.mesasData.filter(m => m.estado === 'ocupada').length;
        const reservadas = this.mesasData.filter(m => m.estado === 'reservada').length;
        const totalVentas = this.mesasData
            .filter(m => m.cuenta_abierta)
            .reduce((sum, m) => sum + m.total_cuenta, 0);

        // Actualizar números
        document.getElementById('widget-disponibles').textContent = disponibles;
        document.getElementById('widget-ocupadas').textContent = ocupadas;
        document.getElementById('widget-reservadas').textContent = reservadas;
        document.getElementById('widget-total').textContent = '$' + totalVentas.toFixed(0);

        // Actualizar lista de mesas ocupadas
        this.actualizarMesasOcupadas();

        // Agregar indicador visual si hay alertas
        this.verificarAlertas();
    }

    actualizarMesasOcupadas() {
        const container = document.getElementById('mesas-ocupadas-items');
        if (!container) return;

        const mesasOcupadas = this.mesasData.filter(m => m.cuenta_abierta);
        
        if (mesasOcupadas.length === 0) {
            container.innerHTML = '<small class="text-muted">No hay mesas ocupadas</small>';
            return;
        }

        container.innerHTML = '';

        mesasOcupadas.forEach(mesa => {
            const tiempoOcupacion = mesa.fecha_apertura ? this.calcularTiempo(mesa.fecha_apertura) : '';
            const esAlerta = this.esMesaConAlerta(mesa);
            
            const mesaItem = document.createElement('div');
            mesaItem.className = `badge ${esAlerta ? 'bg-warning text-dark' : 'bg-primary'} position-relative`;
            mesaItem.style.cursor = 'pointer';
            mesaItem.title = `Mesa ${mesa.numero} - $${mesa.total_cuenta.toFixed(2)} - ${tiempoOcupacion}`;
            mesaItem.onclick = () => this.verCuentaMesa(mesa.id);
            
            mesaItem.innerHTML = `
                ${mesa.numero}
                ${esAlerta ? '<i class="bi bi-exclamation-triangle-fill ms-1"></i>' : ''}
            `;

            container.appendChild(mesaItem);
        });
    }

    esMesaConAlerta(mesa) {
        if (!mesa.fecha_apertura) return false;
        
        const ahora = new Date();
        const apertura = new Date(mesa.fecha_apertura);
        const minutosOcupada = Math.floor((ahora - apertura) / (1000 * 60));
        
        return minutosOcupada >= 90; // Alerta después de 1.5 horas
    }

    verificarAlertas() {
        const mesasConAlerta = this.mesasData.filter(m => this.esMesaConAlerta(m));
        const headerWidget = document.querySelector('#mesas-widget .card-header');
        
        if (mesasConAlerta.length > 0) {
            headerWidget.classList.add('bg-warning');
            headerWidget.classList.remove('bg-light');
            
            // Agregar indicador parpadeante
            if (!headerWidget.querySelector('.alerta-indicator')) {
                const indicator = document.createElement('span');
                indicator.className = 'alerta-indicator badge bg-danger ms-2';
                indicator.style.animation = 'pulse 1s infinite';
                indicator.textContent = mesasConAlerta.length;
                headerWidget.querySelector('h6').appendChild(indicator);
            }
        } else {
            headerWidget.classList.remove('bg-warning');
            headerWidget.classList.add('bg-light');
            
            const indicator = headerWidget.querySelector('.alerta-indicator');
            if (indicator) {
                indicator.remove();
            }
        }
    }

    calcularTiempo(fechaApertura) {
        const ahora = new Date();
        const apertura = new Date(fechaApertura);
        const diff = ahora - apertura;
        
        const horas = Math.floor(diff / (1000 * 60 * 60));
        const minutos = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        
        if (horas > 0) {
            return `${horas}h ${minutos}m`;
        } else {
            return `${minutos}m`;
        }
    }

    toggleWidget() {
        const body = document.getElementById('mesas-widget-body');
        const icon = document.getElementById('widget-toggle-icon');
        
        if (body.style.display === 'none') {
            body.style.display = 'block';
            icon.className = 'bi bi-chevron-up';
        } else {
            body.style.display = 'none';
            icon.className = 'bi bi-chevron-down';
        }
    }

    abrirModalMesas() {
        // Abrir el modal de mesas existente
        const modalMesas = document.getElementById('modalMesas');
        if (modalMesas) {
            const modal = new bootstrap.Modal(modalMesas);
            modal.show();
        }
    }

    crearMesaRapida() {
        const nombre = prompt('Nombre de la nueva mesa (opcional):');
        if (nombre === null) return; // Usuario canceló
        
        const descripcion = prompt('Descripción (opcional):');
        if (descripcion === null) return; // Usuario canceló

        this.crearMesa(nombre || '', descripcion || '');
    }

    async crearMesa(nombre, descripcion) {
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
                this.cargarDatos();
            } else {
                alert('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al crear la mesa');
        }
    }

    verCuentaMesa(mesaId) {
        if (window.gestionMesas) {
            window.gestionMesas.verCuenta(mesaId);
        }
    }

    mostrarNotificacion(mensaje, tipo = 'info') {
        // Usar el sistema de notificaciones de mesas si está disponible
        if (window.notificacionesMesas) {
            window.notificacionesMesas.mostrarNotificacion(mensaje, tipo);
        } else {
            // Fallback a alert simple
            alert(mensaje);
        }
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

    // Método para ocultar/mostrar el widget
    setVisible(visible) {
        const widget = document.getElementById('mesas-widget');
        if (widget) {
            widget.style.display = visible ? 'block' : 'none';
        }
    }

    // Método para obtener estadísticas actuales
    obtenerEstadisticas() {
        return {
            total: this.mesasData.length,
            disponibles: this.mesasData.filter(m => m.estado === 'disponible').length,
            ocupadas: this.mesasData.filter(m => m.estado === 'ocupada').length,
            reservadas: this.mesasData.filter(m => m.estado === 'reservada').length,
            totalVentas: this.mesasData
                .filter(m => m.cuenta_abierta)
                .reduce((sum, m) => sum + m.total_cuenta, 0),
            mesasConAlerta: this.mesasData.filter(m => this.esMesaConAlerta(m)).length
        };
    }
}

// CSS adicional para animaciones
const estilosWidget = `
    <style>
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        #mesas-widget .badge {
            transition: all 0.2s ease;
        }
        
        #mesas-widget .badge:hover {
            transform: scale(1.1);
        }
        
        #mesas-widget .card-header {
            transition: background-color 0.3s ease;
        }
    </style>
`;

// Agregar estilos al head
document.head.insertAdjacentHTML('beforeend', estilosWidget);

// Inicializar cuando el documento esté listo
document.addEventListener('DOMContentLoaded', () => {
    // Solo crear el widget si estamos en la página del POS principal
    if (window.location.pathname === '/pos/' || window.location.pathname.includes('/pos/')) {
        window.mesasWidget = new MesasWidget();
    }
});

// Exportar para uso en otros módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MesasWidget;
}