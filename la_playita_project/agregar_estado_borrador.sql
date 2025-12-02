-- Migración para agregar estado 'borrador' a reabastecimientos
-- Fecha: 2025-01-XX

-- Modificar la columna estado para incluir 'borrador'
ALTER TABLE reabastecimiento 
MODIFY COLUMN estado ENUM('borrador', 'solicitado', 'recibido', 'cancelado') 
DEFAULT 'solicitado';

-- Verificar que la modificación se aplicó correctamente
SELECT COLUMN_TYPE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'reabastecimiento' 
AND COLUMN_NAME = 'estado';
