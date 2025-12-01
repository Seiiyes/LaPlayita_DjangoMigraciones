-- Crear tabla de mesas
CREATE TABLE IF NOT EXISTS mesa (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero VARCHAR(10) UNIQUE NOT NULL,
    nombre VARCHAR(50) DEFAULT '',
    capacidad INT UNSIGNED DEFAULT 4,
    estado VARCHAR(20) DEFAULT 'disponible',
    activa TINYINT(1) DEFAULT 1,
    cuenta_abierta TINYINT(1) DEFAULT 0,
    total_cuenta DECIMAL(12, 2) DEFAULT 0.00,
    fecha_apertura DATETIME NULL,
    cliente_id INT NULL,
    FOREIGN KEY (cliente_id) REFERENCES cliente(id) ON DELETE SET NULL,
    INDEX idx_estado (estado),
    INDEX idx_cuenta_abierta (cuenta_abierta)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Crear tabla de items de mesa
CREATE TABLE IF NOT EXISTS item_mesa (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mesa_id INT NOT NULL,
    producto_id INT NOT NULL,
    lote_id INT NOT NULL,
    cantidad INT UNSIGNED NOT NULL,
    precio_unitario DECIMAL(12, 2) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,
    fecha_agregado DATETIME DEFAULT CURRENT_TIMESTAMP,
    facturado TINYINT(1) DEFAULT 0,
    FOREIGN KEY (mesa_id) REFERENCES mesa(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES producto(id) ON DELETE RESTRICT,
    FOREIGN KEY (lote_id) REFERENCES lote(id) ON DELETE RESTRICT,
    INDEX idx_mesa (mesa_id),
    INDEX idx_facturado (facturado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insertar mesas de ejemplo
INSERT INTO mesa (numero, nombre, capacidad, estado) VALUES
('1', 'Mesa 1', 4, 'disponible'),
('2', 'Mesa 2', 4, 'disponible'),
('3', 'Mesa 3', 6, 'disponible'),
('4', 'Mesa 4', 4, 'disponible'),
('5', 'Mesa 5', 2, 'disponible'),
('6', 'Mesa 6', 4, 'disponible'),
('7', 'Mesa 7', 6, 'disponible'),
('8', 'Mesa 8', 4, 'disponible');
