document.addEventListener('DOMContentLoaded', function () {
    console.log("DOM fully loaded. Attaching event listeners.");

    // Attach the flag to the global window object to ensure it's shared across script executions.
    window.isSaleProcessing = window.isSaleProcessing || false;

    const productList = document.getElementById('product-list');
    const searchInput = document.getElementById('product-search-input');
    const cartTableBody = document.getElementById('cart-table-body');
    const cartEmptyRow = document.getElementById('cart-empty-row');
    const cartTotalSpan = document.getElementById('cart-total');
    const completeSaleButton = document.getElementById('btn-complete-sale');
    const clienteSelect = document.getElementById('cliente-select');
    const metodoPagoSelect = document.getElementById('metodo-pago-select');

    let cart = {};

    console.log("Sale button found:", completeSaleButton);

    // 1. Product Search Functionality
    searchInput.addEventListener('keyup', function () {
        const filter = searchInput.value.toLowerCase();
        const productItems = productList.getElementsByClassName('product-item');
        for (let i = 0; i < productItems.length; i++) {
            const productName = productItems[i].dataset.productName.toLowerCase();
            if (productName.includes(filter)) {
                productItems[i].style.display = '';
            } else {
                productItems[i].style.display = 'none';
            }
        }
    });

    // 2. Add to Cart Functionality
    productList.addEventListener('click', function (e) {
        e.preventDefault();
        const productItem = e.target.closest('.product-item');
        if (!productItem) return;

        const productId = productItem.dataset.productId;
        const stock = parseInt(productItem.dataset.productStock);

        if (cart[productId] && cart[productId].quantity >= stock) {
            alert('No hay más stock disponible para este producto.');
            return;
        }

        if (cart[productId]) {
            cart[productId].quantity++;
        } else {
            cart[productId] = {
                name: productItem.dataset.productName,
                price: parseFloat(productItem.dataset.productPrice),
                quantity: 1,
                stock: stock
            };
        }
        renderCart();
    });

    // 3. Render Cart and Update Totals
    function renderCart() {
        cartTableBody.innerHTML = '';
        let total = 0;

        if (Object.keys(cart).length === 0) {
            cartTableBody.appendChild(cartEmptyRow);
        } else {
            for (const productId in cart) {
                const item = cart[productId];
                const subtotal = item.price * item.quantity;
                total += subtotal;

                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${item.name}</td>
                    <td>
                        <input type="number" class="form-control form-control-sm cart-quantity-input" value="${item.quantity}" min="1" max="${item.stock}" data-product-id="${productId}">
                    </td>
                    <td>${formatCurrency(item.price)}</td>
                    <td>${formatCurrency(subtotal)}</td>
                    <td class="text-center">
                        <button class="btn btn-danger btn-sm remove-from-cart-btn" data-product-id="${productId}">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </td>
                `;
                cartTableBody.appendChild(row);
            }
        }
        cartTotalSpan.textContent = formatCurrency(total);
    }

    // 4. Update quantity or remove from cart
    cartTableBody.addEventListener('change', function(e) {
        if (e.target.classList.contains('cart-quantity-input')) {
            const productId = e.target.dataset.productId;
            let newQuantity = parseInt(e.target.value);

            if (newQuantity > cart[productId].stock) {
                alert('La cantidad no puede superar el stock disponible.');
                newQuantity = cart[productId].stock;
                e.target.value = newQuantity;
            }
            
            if (newQuantity < 1) {
                newQuantity = 1;
                e.target.value = newQuantity;
            }

            cart[productId].quantity = newQuantity;
            renderCart();
        }
    });

    cartTableBody.addEventListener('click', function(e) {
        const removeButton = e.target.closest('.remove-from-cart-btn');
        if (removeButton) {
            const productId = removeButton.dataset.productId;
            delete cart[productId];
            renderCart();
        }
    });

    // 5. Complete Sale Functionality
    completeSaleButton.addEventListener('click', function () {
        console.log("--- 'Finalizar Venta' button clicked. ---");
        console.log("Current processing status (window.isSaleProcessing):", window.isSaleProcessing);

        if (window.isSaleProcessing) {
            console.log("Click ignored because a sale is already processing.");
            return;
        }

        if (Object.keys(cart).length === 0) {
            alert('El carrito está vacío.');
            return;
        }

        console.log("Setting window.isSaleProcessing to true and disabling button.");
        window.isSaleProcessing = true;
        completeSaleButton.disabled = true;
        completeSaleButton.textContent = 'Procesando...';

        const saleData = {
            cliente_id: clienteSelect.value || null,
            metodo_pago: metodoPagoSelect.value,
            items: Object.keys(cart).map(id => ({
                id: id,
                cantidad: cart[id].quantity
            }))
        };

        const csrftoken = getCookie('csrftoken');
        
        console.log("Sending fetch request to /ventas/procesar/ with data:", saleData);

        fetch('/pos/api/procesar-venta/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(saleData)
        })
        .then(response => {
            console.log("Received response from server.");
            return response.json();
        })
        .then(data => {
            console.log("Parsed JSON response:", data);
            if (data.error) {
                alert('Error al procesar la venta: ' + data.error);
                console.log("Resetting form due to error.");
                window.isSaleProcessing = false;
                completeSaleButton.disabled = false;
                completeSaleButton.textContent = 'Finalizar Venta';
            } else {
                // Mostrar modal en lugar de alert
                console.log("Sale successful. Showing invoice modal.");
                showInvoiceModal(data.venta_id);
            }
        })
        .catch(error => {
            console.error('Fetch Error:', error);
            alert('Ocurrió un error de red. Por favor, intente de nuevo.');
            console.log("Resetting form due to network error.");
            window.isSaleProcessing = false;
            completeSaleButton.disabled = false;
            completeSaleButton.textContent = 'Finalizar Venta';
        });
    });

    console.log("Event listener for sale button attached.");

    // Helper function to format currency
    function formatCurrency(value) {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
    }

    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Compact Mode Toggle
    const toggleCompactModeButton = document.getElementById('btn-toggle-compact-mode');
    const productListContainer = document.getElementById('product-list');

    if (toggleCompactModeButton && productListContainer) {
        toggleCompactModeButton.addEventListener('click', function() {
            productListContainer.classList.toggle('compact-mode');

            const icon = toggleCompactModeButton.querySelector('i');
            if (productListContainer.classList.contains('compact-mode')) {
                icon.classList.remove('fa-compress');
                icon.classList.add('fa-expand');
                toggleCompactModeButton.innerHTML = '<i class="fas fa-expand"></i> Modo Normal';
            } else {
                icon.classList.remove('fa-expand');
                icon.classList.add('fa-compress');
                toggleCompactModeButton.innerHTML = '<i class="fas fa-compress"></i> Modo Compacto';
            }
        });
    }

    // Función para mostrar el modal de factura
    function showInvoiceModal(ventaId) {
        const modal = document.getElementById('modalVerFactura');
        const ventaIdSpan = document.getElementById('ventaIdModal');
        const btnVerFactura = document.getElementById('btnVerFactura');
        const btnNoVerFactura = document.getElementById('btnNoVerFactura');

        // Establecer el ID de venta en el modal
        ventaIdSpan.textContent = ventaId;

        // Mostrar el modal
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();

        // Manejar click en "Ver Factura"
        btnVerFactura.onclick = function() {
            // Abrir la factura en una nueva ventana/pestaña
            window.open(`/pos/venta/${ventaId}/factura/`, '_blank');
            bootstrapModal.hide();
            // Recargar la página después de un breve delay
            setTimeout(() => {
                window.location.reload();
            }, 500);
        };

        // Manejar click en "No, gracias"
        btnNoVerFactura.onclick = function() {
            bootstrapModal.hide();
            // Recargar la página
            setTimeout(() => {
                window.location.reload();
            }, 300);
        };

        // También recargar si se cierra el modal de otra forma
        modal.addEventListener('hidden.bs.modal', function() {
            setTimeout(() => {
                window.location.reload();
            }, 300);
        }, { once: true });
    }
});