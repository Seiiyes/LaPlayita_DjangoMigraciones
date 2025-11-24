-- Crear tablas de permisos para el modelo Usuario personalizado

CREATE TABLE IF NOT EXISTS `usuario_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `usuario_id` bigint NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `usuario_groups_usuario_id_group_id_unique` (`usuario_id`,`group_id`),
  KEY `usuario_groups_group_id_fk` (`group_id`),
  CONSTRAINT `usuario_groups_usuario_id_fk` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`),
  CONSTRAINT `usuario_groups_group_id_fk` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `usuario_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `usuario_id` bigint NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `usuario_user_permissions_usuario_id_permission_id_unique` (`usuario_id`,`permission_id`),
  KEY `usuario_user_permissions_permission_id_fk` (`permission_id`),
  CONSTRAINT `usuario_user_permissions_usuario_id_fk` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`),
  CONSTRAINT `usuario_user_permissions_permission_id_fk` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
