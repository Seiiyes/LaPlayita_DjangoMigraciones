#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'la_playita_project.settings')
django.setup()

from django.db import connection

# SQL para crear las tablas
sql_commands = [
    """
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]

# Mesas de ejemplo
mesas = [
    ('1', 'Mesa 1', 4),
    ('2', 'Mesa 2', 4),
    ('3', 'Mesa 3', 6),
    ('4', 'Mesa 4', 4),
    ('5', 'Mesa 5', 2),
    ('6', 'Mesa 6', 4),
    ('7', 'Mesa 7', 6),
    ('8', 'Mesa 8', 4),
]

with connection.cursor() as cursor:
    print("Creando tablas...")
    for sql in sql_commands:
        try:
            cursor.execute(sql)
            print("✓ Tabla creada")
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nInsertando mesas...")
    for numero, nombre, capacidad in mesas:
        try:
            cursor.execute(
                """INSERT INTO mesa (numero, nombre, capacidad, estado, activa, cuenta_abierta, total_cuenta) 
                   VALUES (%s, %s, %s, 'disponible', 1, 0, 0.00)""",
                [numero, nombre, capacidad]
            )
            print(f"✓ {nombre} creada")
        except Exception as e:
            print(f"Mesa {numero} ya existe o error: {e}")

print("\n✓ Proceso completado")
