-- ============================================
-- MIGRACIÓN PQRS - VERSIÓN MEJORADA
-- Sistema presencial con envío de correos
-- ============================================

-- Paso 1: Respaldar datos existentes
CREATE TABLE IF NOT EXISTS `pqrs_backup` AS SELECT * FROM `pqrs`;
CREATE TABLE IF NOT EXISTS `pqrs_evento_backup` AS SELECT * FROM `pqrs_evento`;

-- Paso 2: Eliminar tablas antiguas (deshabilitando constraints temporalmente)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `pqrs_adjunto`;
DROP TABLE IF EXISTS `pqrs_evento`;
DROP TABLE IF EXISTS `pqrs`;
SET FOREIGN_KEY_CHECKS = 1;

-- Paso 3: Crear tabla principal MEJORADA
CREATE TABLE `pqrs` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `numero_caso` varchar(20) NOT NULL UNIQUE,
  `tipo` varchar(20) NOT NULL,
  `categoria` varchar(50) NOT NULL DEFAULT 'general',
  `prioridad` varchar(20) NOT NULL DEFAULT 'media',
  `descripcion` text NOT NULL,
  `estado` varchar(20) DEFAULT 'nuevo',
  `fecha_creacion` datetime NOT NULL DEFAULT current_timestamp(),
  `fecha_actualizacion` datetime DEFAULT NULL ON UPDATE current_timestamp(),
  `fecha_cierre` datetime DEFAULT NULL,
  `cliente_id` bigint(20) NOT NULL,
  `creado_por_id` bigint(20) NOT NULL,
  `ultima_respuesta_enviada` text DEFAULT NULL,
  `correo_enviado` tinyint(1) DEFAULT 0,
  `fecha_ultimo_correo` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_numero_caso` (`numero_caso`),
  KEY `idx_estado` (`estado`),
  KEY `idx_prioridad` (`prioridad`),
  KEY `idx_cliente` (`cliente_id`),
  KEY `idx_creado_por` (`creado_por_id`),
  CONSTRAINT `fk_pqrs_cliente` FOREIGN KEY (`cliente_id`) REFERENCES `cliente` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_pqrs_creado_por` FOREIGN KEY (`creado_por_id`) REFERENCES `usuario` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Paso 4: Crear tabla de eventos MEJORADA
CREATE TABLE `pqrs_evento` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `pqrs_id` bigint(20) NOT NULL,
  `usuario_id` bigint(20) DEFAULT NULL,
  `tipo_evento` varchar(20) NOT NULL,
  `comentario` text DEFAULT NULL,
  `es_visible_cliente` tinyint(1) NOT NULL DEFAULT 1,
  `enviado_por_correo` tinyint(1) DEFAULT 0,
  `fecha_envio_correo` datetime DEFAULT NULL,
  `fecha_evento` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_pqrs` (`pqrs_id`),
  KEY `idx_fecha` (`fecha_evento`),
  KEY `idx_usuario` (`usuario_id`),
  CONSTRAINT `fk_evento_pqrs` FOREIGN KEY (`pqrs_id`) REFERENCES `pqrs` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_evento_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Paso 5: Crear tabla de adjuntos (NUEVA)
CREATE TABLE `pqrs_adjunto` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `pqrs_id` bigint(20) NOT NULL,
  `nombre_archivo` varchar(255) NOT NULL,
  `ruta_archivo` varchar(500) NOT NULL,
  `tipo_mime` varchar(100) NOT NULL,
  `tamano_bytes` bigint(20) NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `subido_por_id` bigint(20) DEFAULT NULL,
  `fecha_subida` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_pqrs` (`pqrs_id`),
  KEY `idx_subido_por` (`subido_por_id`),
  CONSTRAINT `fk_adjunto_pqrs` FOREIGN KEY (`pqrs_id`) REFERENCES `pqrs` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_adjunto_usuario` FOREIGN KEY (`subido_por_id`) REFERENCES `usuario` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Paso 6: Trigger se creará después manualmente
-- Ver archivo: crear_trigger_pqrs.sql

-- Paso 8: Migrar datos antiguos (si existen)
INSERT INTO `pqrs` (
    `id`,
    `numero_caso`,
    `tipo`,
    `categoria`,
    `prioridad`,
    `descripcion`,
    `estado`,
    `fecha_creacion`,
    `fecha_actualizacion`,
    `fecha_cierre`,
    `cliente_id`,
    `creado_por_id`,
    `ultima_respuesta_enviada`,
    `correo_enviado`
)
SELECT 
    pb.id,
    CONCAT('PQRS-', YEAR(pb.fecha_creacion), '-', LPAD(pb.id, 4, '0')) as numero_caso,
    pb.tipo,
    'general' as categoria,
    'media' as prioridad,
    pb.descripcion,
    pb.estado,
    pb.fecha_creacion,
    pb.fecha_actualizacion,
    CASE WHEN pb.estado = 'cerrado' THEN pb.fecha_actualizacion ELSE NULL END as fecha_cierre,
    pb.cliente_id,
    COALESCE(pb.usuario_id, 1) as creado_por_id,
    pb.respuesta as ultima_respuesta_enviada,
    CASE WHEN pb.respuesta IS NOT NULL THEN 1 ELSE 0 END as correo_enviado
FROM `pqrs_backup` pb
WHERE EXISTS (SELECT 1 FROM `pqrs_backup`);

-- Migrar eventos antiguos
INSERT INTO `pqrs_evento` (
    `id`,
    `pqrs_id`,
    `usuario_id`,
    `tipo_evento`,
    `comentario`,
    `es_visible_cliente`,
    `enviado_por_correo`,
    `fecha_evento`
)
SELECT 
    peb.id,
    peb.pqrs_id,
    peb.usuario_id,
    peb.tipo_evento,
    peb.comentario,
    CASE WHEN peb.tipo_evento = 'nota' THEN 0 ELSE 1 END as es_visible_cliente,
    CASE WHEN peb.tipo_evento = 'respuesta' THEN 1 ELSE 0 END as enviado_por_correo,
    peb.fecha_evento
FROM `pqrs_evento_backup` peb
WHERE EXISTS (SELECT 1 FROM `pqrs_evento_backup`);

-- Paso 9: Ajustar el AUTO_INCREMENT
SET @max_id = (SELECT COALESCE(MAX(id), 0) + 1 FROM pqrs);
SET @sql = CONCAT('ALTER TABLE pqrs AUTO_INCREMENT = ', @max_id);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @max_id_evento = (SELECT COALESCE(MAX(id), 0) + 1 FROM pqrs_evento);
SET @sql = CONCAT('ALTER TABLE pqrs_evento AUTO_INCREMENT = ', @max_id_evento);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Paso 10: Verificación
SELECT 'Migración completada exitosamente' as mensaje;
SELECT COUNT(*) as total_pqrs FROM pqrs;
SELECT COUNT(*) as total_eventos FROM pqrs_evento;
SELECT COUNT(*) as total_adjuntos FROM pqrs_adjunto;

-- Paso 11: Opcional - Eliminar backups después de verificar
-- DROP TABLE IF EXISTS `pqrs_backup`;
-- DROP TABLE IF EXISTS `pqrs_evento_backup`;
