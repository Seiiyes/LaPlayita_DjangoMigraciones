// Optimizaciones de performance para crear reabastecimiento

document.addEventListener('DOMContentLoaded', function() {
    // Debounce para cálculos
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Throttle para scroll
    function throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    // Optimizar cálculos de totales con debounce
    const originalCalculateTotals = window.ReabastecimientoForm?.prototype?.calculateTotals;
    if (originalCalculateTotals) {
        window.ReabastecimientoForm.prototype.calculateTotals = debounce(originalCalculateTotals, 150);
    }
    
    // Lazy load de Select2
    const observerOptions = {
        root: null,
        rootMargin: '50px',
        threshold: 0.1
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const select = entry.target;
                if (!select.dataset.select2Initialized && typeof $ !== 'undefined') {
                    $(select).select2({
                        placeholder: 'Buscar...',
                        allowClear: true,
                        width: '100%',
                        dropdownAutoWidth: false,
                        minimumResultsForSearch: 10
                    });
                    select.dataset.select2Initialized = true;
                }
                observer.unobserve(select);
            }
        });
    }, observerOptions);
    
    // Observar selects para lazy loading
    document.querySelectorAll('.select2-field').forEach(select => {
        observer.observe(select);
    });
    
    // Optimizar sincronización de vista móvil
    const originalSyncMobileView = window.ReabastecimientoForm?.prototype?.syncMobileView;
    if (originalSyncMobileView) {
        window.ReabastecimientoForm.prototype.syncMobileView = throttle(originalSyncMobileView, 300);
    }
    
    // Virtualización de filas (solo renderizar visibles)
    const tableBody = document.querySelector('#detalleTable tbody');
    if (tableBody) {
        const rows = Array.from(tableBody.querySelectorAll('tr'));
        const rowHeight = 50; // altura aproximada de cada fila
        const visibleRows = Math.ceil(window.innerHeight / rowHeight) + 2;
        
        let scrollTimeout;
        const handleScroll = throttle(() => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const startIndex = Math.floor(scrollTop / rowHeight);
            const endIndex = startIndex + visibleRows;
            
            rows.forEach((row, index) => {
                if (index >= startIndex && index <= endIndex) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }, 100);
        
        window.addEventListener('scroll', handleScroll);
        handleScroll(); // Initial call
    }
    
    // Optimizar validación con debounce
    document.querySelectorAll('.cantidad-input, .costo-unitario-input').forEach(input => {
        const originalHandler = input.oninput;
        input.oninput = debounce(function(e) {
            if (originalHandler) originalHandler.call(this, e);
        }, 200);
    });
    
    // Reducir repaints en animaciones
    const style = document.createElement('style');
    style.textContent = `
        .formset-row {
            contain: layout style paint;
        }
        
        .reab-table tbody {
            contain: layout;
        }
        
        /* Optimizar Select2 */
        .select2-container {
            will-change: auto;
        }
        
        .select2-dropdown {
            will-change: transform;
            transform: translateZ(0);
        }
    `;
    document.head.appendChild(style);
    
    // Precargar datos de productos en chunks
    const productosData = document.querySelector('script[data-productos]');
    if (productosData) {
        try {
            const productos = JSON.parse(productosData.textContent);
            // Dividir en chunks para no bloquear el thread principal
            const chunkSize = 50;
            let index = 0;
            
            function processChunk() {
                const chunk = productos.slice(index, index + chunkSize);
                // Procesar chunk...
                index += chunkSize;
                
                if (index < productos.length) {
                    requestIdleCallback(processChunk);
                }
            }
            
            if ('requestIdleCallback' in window) {
                requestIdleCallback(processChunk);
            } else {
                setTimeout(processChunk, 0);
            }
        } catch (e) {
            console.error('Error procesando productos:', e);
        }
    }
    
    console.log('✓ Optimizaciones de performance aplicadas');
});
