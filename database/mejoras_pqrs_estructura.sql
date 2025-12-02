-- ============================================================================
-- MEJORAS ESTRUCTURA MÓDULO PQRS
-- Fecha: 2025-12-01
-- Descripción: Optimización de la estructura de datos del módulo PQRS
-- ============================================================================

USE laplayita;

-- ============================================================================
-- PASO 1: ELIMINAR CAMPOS REDUNDANTES DE LA TABLA PQRS
-- ============================================================================

-- Estos campos son redundantes porque la información ya está en pqrs_evento
ALTER TABLE `pqrs` 
DROP COLUMN IF EXISTS `ultima_respuesta_enviada`,
DROP COLUMN IF EXISTS `correo_enviado`,
DROP COLUMN IF EXISTS `fecha_ultimo_correo`;

-- ============================================================================
-- PASO 2: AGREGAR NUEVOS CAMPOS A LA TABLA PQRS
-- ============================================================================

-- Campo para asignar el caso a un operador específico
ALTER TABLE `pqrs` 
ADD COLUMN `asignado_a_id` bigint(20) DEFAULT NULL AFTER `creado_por_id`,
ADD COLUMN `fecha_primera_respuesta` datetime DEFAULT NULL AFTER `fecha_actualizacion`,
ADD COLUMN `tiempo_resolucion_horas` int(11) DEFAULT NULL AFTER `fecha_cierre`,
ADD COLUMN `canal_origen` varchar(20) NOT NULL DEFAULT 'web' AFTER `prioridad`;

-- Agregar índice para asignado_a
ALTER TABLE `pqrs`
ADD INDEX `idx_asignado_a` (`asignado_a_id`),
ADD INDEX `idx_estado_fecha` (`estado`, `fecha_creacion`),
ADD INDEX `idx_canal` (`canal_origen`);

-- Agregar foreign key para asignado_a
ALTER TABLE `pqrs`
ADD CONSTRAINT `fk_pqrs_asignado_a` 
FOREIGN KEY (`asignado_a_id`) REFERENCES `usuario` (`id`) 
ON DELETE SET NULL ON UPDATE CASCADE;

-- ============================================================================
-- PASO 3: CREAR TABLA DE CALIFICACIÓN DEL CLIENTE
-- ============================================================================

DROP TABLE IF EXISTS `pqrs_calificacion`;

CREATE TABLE `pqrs_calificacion` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `pqrs_id` bigint(20) NOT NULL,
  `puntuacion` int(11) NOT NULL COMMENT '1=Muy malo, 2=Malo, 3=Regular, 4=Bueno, 5=Excelente',
  `comentario` text DEFAULT NULL,
  `fecha_calificacion` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_pqrs_calificacion` (`pqrs_id`),
  CONSTRAINT `fk_calificacion_pqrs` 
  FOREIGN KEY (`pqrs_id`) REFERENCES `pqrs` (`id`) 
  ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `chk_puntuacion` CHECK (`puntuacion` >= 1 AND `puntuacion` <= 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- PASO 4: CREAR TABLA DE ESCALAMIENTO (OPCIONAL - PARA FUTURO)
-- ============================================================================

DROP TABLE IF EXISTS `pqrs_escalamiento`;

CREATE TABLE `pqrs_escalamiento` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `pqrs_id` bigint(20) NOT NULL,
  `escalado_por_id` bigint(20) DEFAULT NULL,
  `escalado_a_id` bigint(20) DEFAULT NULL,
  `motivo` text NOT NULL,
  `fecha_escalamiento` datetime NOT NULL DEFAULT current_timestamp(),
  `resuelto` tinyint(1) NOT NULL DEFAULT 0,
  `fecha_resolucion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_pqrs` (`pqrs_id`),
  KEY `idx_escalado_a` (`escalado_a_id`),
  KEY `idx_fecha` (`fecha_escalamiento`),
  CONSTRAINT `fk_escalamiento_pqrs` 
  FOREIGN KEY (`pqrs_id`) REFERENCES `pqrs` (`id`) 
  ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_escalamiento_escalado_por` 
  FOREIGN KEY (`escalado_por_id`) REFERENCES `usuario` (`id`) 
  ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_escalamiento_escalado_a` 
  FOREIGN KEY (`escalado_a_id`) REFERENCES `usuario` (`id`) 
  ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- PASO 5: MEJORAR TRIGGER DE GENERACIÓN DE NÚMERO DE CASO
-- ============================================================================

-- Eliminar trigger existente
DROP TRIGGER IF EXISTS before_insert_pqrs;

DELIMITER $$

CREATE TRIGGER before_insert_pqrs
BEFORE INSERT ON pqrs
FOR EACH ROW
BEGIN
    DECLARE contador INT;
    DECLARE anio INT;
    
    -- Generar número de caso si no existe
    IF NEW.numero_caso IS NULL OR NEW.numero_caso = '' THEN
        SET anio = YEAR(NOW());
        
        -- Usar COALESCE para evitar NULL
        SELECT COALESCE(MAX(CAST(SUBSTRING(numero_caso, -4) AS UNSIGNED)), 0) + 1 
        INTO contador
        FROM pqrs
        WHERE numero_caso LIKE CONCAT('PQRS-', anio, '-%');
        
        SET NEW.numero_caso = CONCAT('PQRS-', anio, '-', LPAD(contador, 4, '0'));
    END IF;
    
    -- Auto-asignar al creador si no hay asignado
    IF NEW.asignado_a_id IS NULL THEN
        SET NEW.asignado_a_id = NEW.creado_por_id;
    END IF;
END$$

DELIMITER ;

-- ============================================================================
-- PASO 6: CREAR TRIGGER PARA CALCULAR TIEMPO DE RESOLUCIÓN
-- ============================================================================

DROP TRIGGER IF EXISTS before_update_pqrs;

DELIMITER $$

CREATE TRIGGER before_update_pqrs
BEFORE UPDATE ON pqrs
FOR EACH ROW
BEGIN
    -- Calcular tiempo de resolución cuando se cierra el caso
    IF NEW.estado = 'cerrado' AND OLD.estado != 'cerrado' THEN
        SET NEW.fecha_cierre = NOW();
        SET NEW.tiempo_resolucion_horas = TIMESTAMPDIFF(HOUR, NEW.fecha_creacion, NOW());
    END IF;
    
    -- Registrar fecha de primera respuesta
    IF NEW.fecha_primera_respuesta IS NULL AND OLD.estado = 'nuevo' AND NEW.estado != 'nuevo' THEN
        SET NEW.fecha_primera_respuesta = NOW();
    END IF;
END$$

DELIMITER ;

-- ============================================================================
-- PASO 7: CREAR VISTA PARA ESTADÍSTICAS RÁPIDAS
-- ============================================================================

DROP VIEW IF EXISTS v_pqrs_estadisticas;

CREATE VIEW v_pqrs_estadisticas AS
SELECT 
    COUNT(*) as total_casos,
    SUM(CASE WHEN estado = 'nuevo' THEN 1 ELSE 0 END) as casos_nuevos,
    SUM(CASE WHEN estado = 'en_proceso' THEN 1 ELSE 0 END) as casos_en_proceso,
    SUM(CASE WHEN estado = 'resuelto' THEN 1 ELSE 0 END) as casos_resueltos,
    SUM(CASE WHEN estado = 'cerrado' THEN 1 ELSE 0 END) as casos_cerrados,
    SUM(CASE WHEN prioridad = 'urgente' THEN 1 ELSE 0 END) as casos_urgentes,
    SUM(CASE WHEN prioridad = 'alta' THEN 1 ELSE 0 END) as casos_alta_prioridad,
    AVG(tiempo_resolucion_horas) as tiempo_promedio_resolucion_horas,
    COUNT(DISTINCT cliente_id) as clientes_unicos,
    SUM(CASE WHEN fecha_creacion >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) as casos_ultima_semana,
    SUM(CASE WHEN fecha_creacion >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 ELSE 0 END) as casos_ultimo_mes
FROM pqrs;

-- ============================================================================
-- PASO 8: CREAR VISTA PARA CASOS ASIGNADOS POR USUARIO
-- ============================================================================

DROP VIEW IF EXISTS v_pqrs_por_usuario;

CREATE VIEW v_pqrs_por_usuario AS
SELECT 
    u.id as usuario_id,
    u.username,
    u.nombres,
    u.apellidos,
    COUNT(p.id) as total_casos_asignados,
    SUM(CASE WHEN p.estado = 'nuevo' THEN 1 ELSE 0 END) as casos_nuevos,
    SUM(CASE WHEN p.estado = 'en_proceso' THEN 1 ELSE 0 END) as casos_en_proceso,
    SUM(CASE WHEN p.estado = 'resuelto' THEN 1 ELSE 0 END) as casos_resueltos,
    SUM(CASE WHEN p.estado = 'cerrado' THEN 1 ELSE 0 END) as casos_cerrados,
    AVG(p.tiempo_resolucion_horas) as tiempo_promedio_resolucion
FROM usuario u
LEFT JOIN pqrs p ON u.id = p.asignado_a_id
GROUP BY u.id, u.username, u.nombres, u.apellidos;

-- ============================================================================
-- PASO 9: MIGRAR DATOS EXISTENTES (SI HAY)
-- ============================================================================

-- Auto-asignar casos existentes al creador si no tienen asignado
UPDATE pqrs 
SET asignado_a_id = creado_por_id 
WHERE asignado_a_id IS NULL;

-- Calcular tiempo de resolución para casos ya cerrados
UPDATE pqrs 
SET tiempo_resolucion_horas = TIMESTAMPDIFF(HOUR, fecha_creacion, fecha_cierre)
WHERE estado = 'cerrado' 
AND fecha_cierre IS NOT NULL 
AND tiempo_resolucion_horas IS NULL;

-- ============================================================================
-- PASO 10: VERIFICACIÓN DE LA ESTRUCTURA
-- ============================================================================

-- Verificar que las tablas existen
SELECT 'Verificando estructura...' as mensaje;

SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    CREATE_TIME,
    UPDATE_TIME
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'laplayita'
AND TABLE_NAME LIKE 'pqrs%'
ORDER BY TABLE_NAME;

-- Verificar columnas de la tabla principal
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    COLUMN_KEY
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'laplayita'
AND TABLE_NAME = 'pqrs'
ORDER BY ORDINAL_POSITION;

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================

SELECT '✅ Script ejecutado exitosamente' as resultado;
SELECT 'Estructura PQRS optimizada y lista para usar' as mensaje;
