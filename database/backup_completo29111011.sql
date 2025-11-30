/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-12.0.2-MariaDB, for Win64 (AMD64)
--
-- Host: localhost    Database: laplayita
-- ------------------------------------------------------
-- Server version	12.0.2-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Current Database: `laplayita`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `laplayita` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_uca1400_ai_ci */;

USE `laplayita`;

--
-- Table structure for table `auditoria_reabastecimiento`
--

DROP TABLE IF EXISTS `auditoria_reabastecimiento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auditoria_reabastecimiento` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `reabastecimiento_id` bigint(20) NOT NULL,
  `usuario_id` bigint(20) DEFAULT NULL,
  `accion` varchar(20) NOT NULL,
  `cantidad_anterior` int(11) DEFAULT NULL,
  `cantidad_nueva` int(11) DEFAULT NULL,
  `descripcion` longtext DEFAULT NULL,
  `fecha` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_reabastecimiento` (`reabastecimiento_id`),
  KEY `idx_fecha` (`fecha`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auditoria_reabastecimiento`
--

LOCK TABLES `auditoria_reabastecimiento` WRITE;
/*!40000 ALTER TABLE `auditoria_reabastecimiento` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `auditoria_reabastecimiento` VALUES
(1,61,2,'recibido',NULL,23,'Recepción completada: 1 productos recibidos','2025-11-29 23:55:48');
/*!40000 ALTER TABLE `auditoria_reabastecimiento` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=113 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `auth_permission` VALUES
(1,'Can add permission',1,'add_permission'),
(2,'Can change permission',1,'change_permission'),
(3,'Can delete permission',1,'delete_permission'),
(4,'Can view permission',1,'view_permission'),
(5,'Can add group',2,'add_group'),
(6,'Can change group',2,'change_group'),
(7,'Can delete group',2,'delete_group'),
(8,'Can view group',2,'view_group'),
(9,'Can add content type',3,'add_contenttype'),
(10,'Can change content type',3,'change_contenttype'),
(11,'Can delete content type',3,'delete_contenttype'),
(12,'Can view content type',3,'view_contenttype'),
(13,'Can add session',4,'add_session'),
(14,'Can change session',4,'change_session'),
(15,'Can delete session',4,'delete_session'),
(16,'Can view session',4,'view_session'),
(17,'Can add rol',5,'add_rol'),
(18,'Can change rol',5,'change_rol'),
(19,'Can delete rol',5,'delete_rol'),
(20,'Can view rol',5,'view_rol'),
(21,'Can add usuario',6,'add_usuario'),
(22,'Can change usuario',6,'change_usuario'),
(23,'Can delete usuario',6,'delete_usuario'),
(24,'Can view usuario',6,'view_usuario'),
(25,'Can add log entry',7,'add_logentry'),
(26,'Can change log entry',7,'change_logentry'),
(27,'Can delete log entry',7,'delete_logentry'),
(28,'Can view log entry',7,'view_logentry'),
(29,'Can add categoria',8,'add_categoria'),
(30,'Can change categoria',8,'change_categoria'),
(31,'Can delete categoria',8,'delete_categoria'),
(32,'Can view categoria',8,'view_categoria'),
(33,'Can add lote',9,'add_lote'),
(34,'Can change lote',9,'change_lote'),
(35,'Can delete lote',9,'delete_lote'),
(36,'Can view lote',9,'view_lote'),
(37,'Can add movimiento inventario',10,'add_movimientoinventario'),
(38,'Can change movimiento inventario',10,'change_movimientoinventario'),
(39,'Can delete movimiento inventario',10,'delete_movimientoinventario'),
(40,'Can view movimiento inventario',10,'view_movimientoinventario'),
(41,'Can add producto',11,'add_producto'),
(42,'Can change producto',11,'change_producto'),
(43,'Can delete producto',11,'delete_producto'),
(44,'Can view producto',11,'view_producto'),
(45,'Can add pago',12,'add_pago'),
(46,'Can change pago',12,'change_pago'),
(47,'Can delete pago',12,'delete_pago'),
(48,'Can view pago',12,'view_pago'),
(49,'Can add pedido',13,'add_pedido'),
(50,'Can change pedido',13,'change_pedido'),
(51,'Can delete pedido',13,'delete_pedido'),
(52,'Can view pedido',13,'view_pedido'),
(53,'Can add pedido detalle',14,'add_pedidodetalle'),
(54,'Can change pedido detalle',14,'change_pedidodetalle'),
(55,'Can delete pedido detalle',14,'delete_pedidodetalle'),
(56,'Can view pedido detalle',14,'view_pedidodetalle'),
(57,'Can add venta',15,'add_venta'),
(58,'Can change venta',15,'change_venta'),
(59,'Can delete venta',15,'delete_venta'),
(60,'Can view venta',15,'view_venta'),
(61,'Can add venta detalle',16,'add_ventadetalle'),
(62,'Can change venta detalle',16,'change_ventadetalle'),
(63,'Can delete venta detalle',16,'delete_ventadetalle'),
(64,'Can view venta detalle',16,'view_ventadetalle'),
(65,'Can add pqrs',17,'add_pqrs'),
(66,'Can change pqrs',17,'change_pqrs'),
(67,'Can delete pqrs',17,'delete_pqrs'),
(68,'Can view pqrs',17,'view_pqrs'),
(69,'Can add pqrs historial',18,'add_pqrshistorial'),
(70,'Can change pqrs historial',18,'change_pqrshistorial'),
(71,'Can delete pqrs historial',18,'delete_pqrshistorial'),
(72,'Can view pqrs historial',18,'view_pqrshistorial'),
(73,'Can add proveedor',19,'add_proveedor'),
(74,'Can change proveedor',19,'change_proveedor'),
(75,'Can delete proveedor',19,'delete_proveedor'),
(76,'Can view proveedor',19,'view_proveedor'),
(77,'Can add reabastecimiento',20,'add_reabastecimiento'),
(78,'Can change reabastecimiento',20,'change_reabastecimiento'),
(79,'Can delete reabastecimiento',20,'delete_reabastecimiento'),
(80,'Can view reabastecimiento',20,'view_reabastecimiento'),
(81,'Can add reabastecimiento detalle',21,'add_reabastecimientodetalle'),
(82,'Can change reabastecimiento detalle',21,'change_reabastecimientodetalle'),
(83,'Can delete reabastecimiento detalle',21,'delete_reabastecimientodetalle'),
(84,'Can view reabastecimiento detalle',21,'view_reabastecimientodetalle'),
(85,'Can add Cliente',22,'add_cliente'),
(86,'Can change Cliente',22,'change_cliente'),
(87,'Can delete Cliente',22,'delete_cliente'),
(88,'Can view Cliente',22,'view_cliente'),
(89,'Can add pqrs evento',23,'add_pqrsevento'),
(90,'Can change pqrs evento',23,'change_pqrsevento'),
(91,'Can delete pqrs evento',23,'delete_pqrsevento'),
(92,'Can view pqrs evento',23,'view_pqrsevento'),
(93,'Can add producto canjeble',24,'add_productocanjeble'),
(94,'Can change producto canjeble',24,'change_productocanjeble'),
(95,'Can delete producto canjeble',24,'delete_productocanjeble'),
(96,'Can view producto canjeble',24,'view_productocanjeble'),
(97,'Can add canje producto',25,'add_canjeproducto'),
(98,'Can change canje producto',25,'change_canjeproducto'),
(99,'Can delete canje producto',25,'delete_canjeproducto'),
(100,'Can view canje producto',25,'view_canjeproducto'),
(101,'Can add puntos fidelizacion',26,'add_puntosfidelizacion'),
(102,'Can change puntos fidelizacion',26,'change_puntosfidelizacion'),
(103,'Can delete puntos fidelizacion',26,'delete_puntosfidelizacion'),
(104,'Can view puntos fidelizacion',26,'view_puntosfidelizacion'),
(105,'Can add auditoria reabastecimiento',27,'add_auditoriareabastecimiento'),
(106,'Can change auditoria reabastecimiento',27,'change_auditoriareabastecimiento'),
(107,'Can delete auditoria reabastecimiento',27,'delete_auditoriareabastecimiento'),
(108,'Can view auditoria reabastecimiento',27,'view_auditoriareabastecimiento'),
(109,'Can add tasa iva',28,'add_tasaiva'),
(110,'Can change tasa iva',28,'change_tasaiva'),
(111,'Can delete tasa iva',28,'delete_tasaiva'),
(112,'Can view tasa iva',28,'view_tasaiva');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `canje_producto`
--

DROP TABLE IF EXISTS `canje_producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `canje_producto` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `puntos_gastados` decimal(10,2) NOT NULL,
  `fecha_canje` datetime(6) NOT NULL,
  `estado` varchar(20) NOT NULL,
  `fecha_entrega` datetime(6) DEFAULT NULL,
  `cliente_id` bigint(20) NOT NULL,
  `producto_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `canje_producto`
--

LOCK TABLES `canje_producto` WRITE;
/*!40000 ALTER TABLE `canje_producto` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `canje_producto` VALUES
(1,3.69,'2025-11-23 06:38:15.185869','completado',NULL,6,1),
(2,3.69,'2025-11-23 06:39:42.102779','completado',NULL,6,1),
(3,3.69,'2025-11-24 15:15:13.804939','completado',NULL,3,1);
/*!40000 ALTER TABLE `canje_producto` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `categoria`
--

DROP TABLE IF EXISTS `categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `categoria` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(25) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categoria`
--

LOCK TABLES `categoria` WRITE;
/*!40000 ALTER TABLE `categoria` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `categoria` VALUES
(1,'Lacteos'),
(2,'Quesos'),
(3,'Cerveza'),
(4,'Gaseosa'),
(5,'Dulces'),
(6,'paquetes');
/*!40000 ALTER TABLE `categoria` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `cliente`
--

DROP TABLE IF EXISTS `cliente`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `cliente` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `documento` varchar(20) NOT NULL,
  `nombres` varchar(50) NOT NULL,
  `apellidos` varchar(50) NOT NULL,
  `correo` varchar(60) NOT NULL,
  `telefono` varchar(25) NOT NULL,
  `puntos_totales` decimal(10,2) DEFAULT 0.00,
  PRIMARY KEY (`id`),
  UNIQUE KEY `documento` (`documento`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cliente`
--

LOCK TABLES `cliente` WRITE;
/*!40000 ALTER TABLE `cliente` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `cliente` VALUES
(1,'12345678','Pepito','Perez','pepito@gmail.com','12342155124',0.00),
(2,'10001','Laura','Martinez','laura.m@gmail.com','3124567890',0.00),
(3,'213213','Michael David ','Ramirez','richardodito@gmail.com','3503372482',5.02),
(5,'2343422','Juan andres','Lizarazo','liza@gmail.com','35223234234',0.00),
(6,'ADMIN-4','Laura','Gomez','laura.admin@laplayita.com','0000000000',9992.62),
(7,'100038243432','cecilia','Rodriguez','liza@gmail.com','32423424',0.00);
/*!40000 ALTER TABLE `cliente` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL CHECK (`action_flag` >= 0),
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `django_content_type` VALUES
(7,'admin','logentry'),
(2,'auth','group'),
(1,'auth','permission'),
(25,'clients','canjeproducto'),
(22,'clients','cliente'),
(24,'clients','productocanjeble'),
(26,'clients','puntosfidelizacion'),
(3,'contenttypes','contenttype'),
(8,'inventory','categoria'),
(9,'inventory','lote'),
(10,'inventory','movimientoinventario'),
(11,'inventory','producto'),
(28,'inventory','tasaiva'),
(12,'pos','pago'),
(13,'pos','pedido'),
(14,'pos','pedidodetalle'),
(15,'pos','venta'),
(16,'pos','ventadetalle'),
(17,'pqrs','pqrs'),
(23,'pqrs','pqrsevento'),
(18,'pqrs','pqrshistorial'),
(4,'sessions','session'),
(27,'suppliers','auditoriareabastecimiento'),
(19,'suppliers','proveedor'),
(20,'suppliers','reabastecimiento'),
(21,'suppliers','reabastecimientodetalle'),
(5,'users','rol'),
(6,'users','usuario');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `django_migrations` VALUES
(1,'contenttypes','0001_initial','2025-11-19 01:51:29.183102'),
(2,'contenttypes','0002_remove_content_type_name','2025-11-19 01:51:29.235134'),
(3,'auth','0001_initial','2025-11-19 01:51:29.406066'),
(4,'auth','0002_alter_permission_name_max_length','2025-11-19 01:51:29.442857'),
(5,'auth','0003_alter_user_email_max_length','2025-11-19 01:51:29.448597'),
(6,'auth','0004_alter_user_username_opts','2025-11-19 01:51:29.453729'),
(7,'auth','0005_alter_user_last_login_null','2025-11-19 01:51:29.458824'),
(8,'auth','0006_require_contenttypes_0002','2025-11-19 01:51:29.461046'),
(9,'auth','0007_alter_validators_add_error_messages','2025-11-19 01:51:29.465838'),
(10,'auth','0008_alter_user_username_max_length','2025-11-19 01:51:29.470411'),
(11,'auth','0009_alter_user_last_name_max_length','2025-11-19 01:51:29.474934'),
(12,'auth','0010_alter_group_name_max_length','2025-11-19 01:51:29.498844'),
(13,'auth','0011_update_proxy_permissions','2025-11-19 01:51:29.503925'),
(14,'auth','0012_alter_user_first_name_max_length','2025-11-19 01:51:29.508934'),
(15,'sessions','0001_initial','2025-11-19 01:53:03.615302'),
(16,'users','0001_initial','2025-11-19 02:05:50.226802'),
(17,'suppliers','0001_initial','2025-11-19 02:07:00.029220'),
(18,'inventory','0001_initial','2025-11-19 02:07:24.792645'),
(19,'pos','0001_initial','2025-11-19 02:07:31.550654'),
(20,'core','0001_initial','2025-11-19 02:07:40.059590'),
(21,'pqrs','0001_initial','2025-11-19 02:07:54.810440'),
(22,'clients','0001_initial','2025-11-19 02:08:04.428007'),
(23,'admin','0001_initial','2025-11-19 02:13:44.480599'),
(24,'admin','0002_logentry_remove_auto_add','2025-11-19 02:13:44.486783'),
(25,'admin','0003_logentry_add_action_flag_choices','2025-11-19 02:13:44.493026'),
(26,'clients','0002_initial','2025-11-19 12:19:52.940673'),
(27,'inventory','0002_initial','2025-11-19 12:19:52.955620'),
(28,'pos','0002_initial','2025-11-19 12:19:52.962756'),
(29,'pqrs','0002_initial','2025-11-19 12:19:52.968056'),
(30,'suppliers','0002_initial','2025-11-19 12:19:52.973037'),
(31,'users','0002_alter_rol_options_alter_usuario_is_superuser','2025-11-19 12:19:52.988441'),
(32,'users','0003_usuario_is_staff','2025-11-19 13:11:08.531443'),
(33,'users','0004_manual_add_is_superuser','2025-11-19 13:14:21.160191'),
(34,'pos','0003_fix_trigger_stock_update','2025-11-22 05:30:57.994689'),
(35,'clients','0003_add_loyalty_system','2025-11-22 05:53:08.157482'),
(36,'clients','0004_create_loyalty_tables','2025-11-22 06:24:07.640028'),
(37,'pqrs','0003_pqrsevento_delete_pqrshistorial_alter_pqrs_options_and_more','2025-11-24 01:50:15.942398'),
(38,'pqrs','0004_alter_pqrs_options_alter_pqrsevento_pqrs_and_more','2025-11-24 01:50:16.380649'),
(39,'users','0005_alter_usuario_id','2025-11-24 01:50:16.398830'),
(40,'clients','0005_productocanjeble_producto_inventario','2025-11-24 15:14:20.593254'),
(41,'users','0006_create_permission_tables','2025-11-24 15:14:30.251788'),
(42,'suppliers','0003_add_audit_fields','2025-11-29 21:38:40.718480'),
(43,'suppliers','0004_add_audit_and_lote','2025-11-29 21:52:46.180588'),
(44,'inventory','0003_tasaiva','2025-11-29 21:59:47.634431'),
(45,'suppliers','0005_auditoriareabastecimiento','2025-11-29 21:59:47.636875');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `django_session` VALUES
('0ease78l1wxvtqn6kf2ow7pzv994a4jw','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vONeg:1Ntdn9iGektcfSHfIStjNW9vy3tCeiSLlPsexI7LsQ4','2025-11-26 22:36:30.643362'),
('168v9zedcwtb983qn9p83t7rq1dwmrg2','.eJxVjLsOwjAMAP_FM4poEvLoyM43VLbjkAJKpKadEP-OKnWA9e50b5hwW8u0dVmmOcEIDk6_jJCfUneRHljvTXGr6zKT2hN12K5uLcnrerR_g4K9wAjZh0FH5kxeDJoYM12Ct2eNRrM2niSQsDjOQ_QU2AW2ZAVNziYGTPD5Avx4OOE:1vMgJK:2ISjvAyL9fNsmdeeaHsGl6SaEiZAwnEeTXJv6SLEjGk','2025-12-06 05:37:26.534237'),
('1819zifalcahqpcl4lei3odrlyc2g7sk','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vNkqV:ctoGKctU9Itni_fQAyQCvfLU4gJfUIZ_0h7r4Aub7lQ','2025-11-25 05:10:07.252966'),
('4trrzi4g22irkpl1etyimljfzooq3ijy','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vMPTJ:TjtJ8nwgay9XJdG1twYwR0z-7FHM1DObJsyMLcOl2Yo','2025-12-05 11:38:37.434948'),
('6bbvndspopyye0spt2fvrw2snw7zes9z','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vNhC2:1mu5GW3rhPA-nSSLvAtKnVCAJSqFj1-aMKN6KrsYodE','2025-11-25 01:16:06.815132'),
('76d2geff1mkrytu8o0hlmd3nxm51hptf','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vNUdN:XyFRmS_FayAp7-0f2Ewg0hHc7odnVGzRS0DwHNwFDLU','2025-12-08 11:21:29.226077'),
('7uy20k0zjobylaucwb7084nyhskj47wb','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vPAX3:d85aSxsiPjvUspyJFRJrNGynpyCN63z1ObWD7UL9rdQ','2025-11-29 02:47:53.446763'),
('8ynchq1evtb92l5f9rjq1u1pzaa7168v','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vLhE2:-cgsp0Yso0dZgftgjeO4Ynpd7X2B-GaCNlWZxxFEv7c','2025-12-03 12:23:54.454513'),
('9uz8sea8hry2pcn9frx7w3c4mh4wu3w2','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vPQcK:OopjG6ODSpg7goNBquTFUFNXTzzxMu2GhOzaz7lkwt4','2025-11-29 19:58:24.714172'),
('a1x5vko5f0j67vy80cvp05iplkzgfqqt','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vPBh4:hW0oiva_kXzOYLgmIw7gOh5RbRpf6zUpkt2CaFhi34I','2025-11-29 04:02:18.848624'),
('ed8wopbkvuauyh1hhjsqumapx2kmvwr6','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vOqCv:CcBlKAKd3vncrKZ7T5DEkenAWbucXIX0TfAbPVgJ3Wc','2025-11-28 05:05:45.070120'),
('gp4elbrcnjxugkpj88y7daru8a9genra','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vOjne:lrT2GR8WRCVywRlpw8Z4Qzb5XS14tqFfdSCmCSEbuUo','2025-11-27 22:15:14.412967'),
('in6w6e7vcc3n48tyh7gephu4kjyfmm28','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vN3JY:4VFhBYDSV9MkfUMwOockM_95M5st8m88HggWKzXq_fM','2025-12-07 06:11:12.249463'),
('na5a7mz0edr5h31os1w4mxzkm3hdpsy3','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vPXY9:WWrBk0SaGFZQ5DvqqPlhi-PQSpgYeDJyaWeihC7HM4U','2025-11-30 03:22:33.087133'),
('npi7w04qfqo00zm57xl0up92yvfk8s3s','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vOo71:4bOZTAIeyQQphpGhrS49L5SrpH8YKasfGWfbmFw293g','2025-11-28 02:51:31.484627'),
('ojy1o12h1hxmeut1881sznofgk6k59mg','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vNlde:mA2PaUpPW4ZgYc4NFwpu0McIcLPZQ-py2CMq8moJcUc','2025-11-25 06:00:54.926883'),
('ptgiumf1zjnplxbec66fkdi33y52ma4l','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vP39j:TbEXWXrRkKwDHRIlGecXDPJl4Y8gs3p2Lvz5LsB-w1Y','2025-11-28 18:55:19.054383'),
('si4dhixeiquo78m4rfz83gfc2lzv0azt','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vOp5N:SgjsFs--W2iQJTKekn430Q1dUtDccgFuZ9avkIL7bok','2025-11-28 03:53:53.196394'),
('ts2oiw4b15ei2bp1ax7llo8j6j1nt9ew','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vPUsS:uRPLrBA08U6uCUl5vlOjt_8ti58i_UUroUXYckubbJc','2025-11-30 00:31:20.582897'),
('vgerxkbm0jp328vuujjys69p5c1s73yf','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vNe7d:Y2f8TY4qpdVaXr37NyjfWZe1p-m6NayuEeS5qPDsb4A','2025-11-24 21:59:21.961321'),
('vi5yxdtugyu9xt83w58qykpqlyzbb8r1','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vOOHp:a5m07DbUsocplnI4xDsTZacoRQFcr8glqSNmzBXG21Y','2025-11-26 23:16:57.423774'),
('vp9pys04aec4bsadqykjt2i6dslld2s1','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vOl9p:sjFKFVOZsIL2GOcx0xXM9kG6stHcIM7pKBzATfBRBlU','2025-11-27 23:42:13.529654'),
('w7vaikmjpfm17jqfzmeljxl518he9aez','.eJxVjDsOAiEUAO9CbQjyx9LeM5AHjyerBpJltzLe3ZBsoe3MZN4swr7VuI-yxgXZhWl2-mUJ8rO0KfAB7d557m1bl8Rnwg87-K1jeV2P9m9QYdS5JZsdaY1ZmaCMCsI4KTBQkkGADMUGe1ZaeKnAF7KETtgEmrQr4JJnny_F9Ddd:1vPBXZ:Frg2ecjVM6uCgxt-vlqPN0CDBEejnZ6NxtwMq6Scd_M','2025-11-29 03:52:29.564041');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `lote`
--

DROP TABLE IF EXISTS `lote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lote` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `producto_id` int(11) NOT NULL,
  `reabastecimiento_detalle_id` int(11) DEFAULT NULL,
  `numero_lote` varchar(50) NOT NULL,
  `cantidad_disponible` int(11) unsigned NOT NULL,
  `costo_unitario_lote` decimal(12,2) NOT NULL,
  `fecha_caducidad` date NOT NULL,
  `fecha_entrada` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_lote_producto_numero` (`producto_id`,`numero_lote`),
  KEY `fk_lote_producto` (`producto_id`),
  KEY `fk_lote_reabastecimiento_detalle` (`reabastecimiento_detalle_id`),
  CONSTRAINT `fk_lote_producto` FOREIGN KEY (`producto_id`) REFERENCES `producto` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_lote_reabastecimiento_detalle` FOREIGN KEY (`reabastecimiento_detalle_id`) REFERENCES `reabastecimiento_detalle` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lote`
--

LOCK TABLES `lote` WRITE;
/*!40000 ALTER TABLE `lote` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `lote` VALUES
(1,1,1,'LCH-A1',0,2500.00,'2025-10-30','2025-09-01 10:00:00'),
(2,2,2,'QSO-C3',48,7000.00,'2025-11-15','2025-09-05 14:00:00'),
(3,7,38,'R36-P7-38',29,4500.00,'2025-12-31','2025-11-05 11:38:47'),
(4,8,39,'R37-P8-39',0,2500.00,'2025-12-06','2025-11-05 13:45:41'),
(5,7,42,'R40-P7-42',199,4500.00,'2026-01-15','2025-11-06 23:06:20'),
(6,7,40,'R38-P7-40',100,4500.00,'2026-01-17','2025-11-06 23:08:20'),
(7,1,45,'R45-P1-45',5,3800.00,'2026-01-10','2025-11-12 22:46:31'),
(10,3,55,'R55-P3-55',199,3000.00,'2026-01-03','2025-11-19 13:20:32'),
(14,11,58,'R58-P11-58',16,3000.00,'2025-11-29','2025-11-21 11:50:44'),
(15,12,59,'R59-P12-59',43,3500.00,'2025-11-29','2025-11-21 12:10:34'),
(17,9,46,'R46-P9-46',99,3000.00,'2026-02-12','2025-11-24 00:23:01'),
(18,9,60,'R60-P9-60',22,3000.00,'2026-01-01','2025-11-24 15:06:00'),
(19,1,61,'R61-P1-61',23,3800.00,'2025-12-31','2025-11-29 23:25:07'),
(20,10,80,'R80-P10-80',89,5000.00,'2026-01-01','2025-11-30 02:52:22');
/*!40000 ALTER TABLE `lote` ENABLE KEYS */;
UNLOCK TABLES;
commit;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_uca1400_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_lote_after_insert
AFTER INSERT ON lote
FOR EACH ROW
BEGIN
  UPDATE producto
    SET stock_actual = stock_actual + NEW.cantidad_disponible
    WHERE id = NEW.producto_id;

  CALL sp_recalcular_costo_promedio_por_producto(NEW.producto_id);
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_uca1400_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_lote_after_update
            AFTER UPDATE ON lote
            FOR EACH ROW
            BEGIN
              DECLARE diff INT;
              SET diff = CAST(NEW.cantidad_disponible AS SIGNED) - CAST(OLD.cantidad_disponible AS SIGNED);
              IF diff <> 0 THEN
                UPDATE producto
                  SET stock_actual = stock_actual + diff
                  WHERE id = NEW.producto_id;
              END IF;

              IF NEW.producto_id <> OLD.producto_id THEN
                CALL sp_recalcular_costo_promedio_por_producto(OLD.producto_id);
                CALL sp_recalcular_costo_promedio_por_producto(NEW.producto_id);
              ELSE
                CALL sp_recalcular_costo_promedio_por_producto(NEW.producto_id);
              END IF;
            END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_uca1400_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_lote_after_delete
AFTER DELETE ON lote
FOR EACH ROW
BEGIN
  UPDATE producto
    SET stock_actual = stock_actual - OLD.cantidad_disponible
    WHERE id = OLD.producto_id;

  CALL sp_recalcular_costo_promedio_por_producto(OLD.producto_id);
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `movimiento_inventario`
--

DROP TABLE IF EXISTS `movimiento_inventario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `movimiento_inventario` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `producto_id` int(11) NOT NULL,
  `lote_id` int(11) DEFAULT NULL,
  `cantidad` int(11) NOT NULL,
  `tipo_movimiento` varchar(20) NOT NULL,
  `fecha_movimiento` datetime NOT NULL DEFAULT current_timestamp(),
  `descripcion` varchar(255) DEFAULT NULL,
  `venta_id` int(11) DEFAULT NULL,
  `reabastecimiento_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `producto_id` (`producto_id`),
  KEY `lote_id` (`lote_id`),
  KEY `venta_id` (`venta_id`),
  KEY `reabastecimiento_id` (`reabastecimiento_id`),
  CONSTRAINT `fk_movimiento_inventario_lote` FOREIGN KEY (`lote_id`) REFERENCES `lote` (`id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_movimiento_inventario_producto` FOREIGN KEY (`producto_id`) REFERENCES `producto` (`id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_movimiento_inventario_reabastecimiento` FOREIGN KEY (`reabastecimiento_id`) REFERENCES `reabastecimiento` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_movimiento_inventario_venta` FOREIGN KEY (`venta_id`) REFERENCES `venta` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `movimiento_inventario`
--

LOCK TABLES `movimiento_inventario` WRITE;
/*!40000 ALTER TABLE `movimiento_inventario` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `movimiento_inventario` VALUES
(1,1,1,100,'ENTRADA','2025-10-10 22:48:22','Reabastecimiento inicial Lote A1',NULL,1),
(2,2,2,60,'ENTRADA','2025-10-10 22:48:22','Reabastecimiento inicial Lote C3',NULL,1),
(3,1,1,-2,'SALIDA','2025-10-10 22:48:22','Venta ID 1',1,NULL),
(4,2,2,-1,'SALIDA','2025-10-10 22:48:22','Venta ID 2',2,NULL),
(5,7,3,60,'entrada','2025-11-05 11:38:47','Entrada por reabastecimiento #36',NULL,36),
(6,7,3,-1,'salida','2025-11-05 12:40:34','Venta #6',6,NULL),
(7,1,1,-6,'salida','2025-11-05 12:44:58','Venta #7',7,NULL),
(8,8,4,10,'entrada','2025-11-05 13:45:41','Entrada por reabastecimiento #37',NULL,37),
(9,8,4,-10,'salida','2025-11-05 13:48:30','Venta #8',8,NULL),
(10,7,3,-4,'salida','2025-11-06 22:52:29','Venta #9',9,NULL),
(11,7,5,199,'entrada','2025-11-06 23:06:20','Entrada por reabastecimiento #40',NULL,40),
(12,7,6,100,'entrada','2025-11-06 23:08:20','Entrada por reabastecimiento #38',NULL,38),
(13,1,7,5,'entrada','2025-11-12 22:46:31','Entrada por reabastecimiento #45',NULL,45),
(16,3,10,199,'entrada','2025-11-19 13:20:32','Entrada por reabastecimiento #55',NULL,55),
(18,11,14,55,'entrada','2025-11-21 11:50:44','Entrada por reabastecimiento #58',NULL,58),
(19,12,15,43,'entrada','2025-11-21 12:10:34','Entrada por reabastecimiento #59',NULL,59),
(20,9,17,99,'entrada','2025-11-24 00:23:01','Entrada por reabastecimiento #46',NULL,46),
(21,9,18,22,'entrada','2025-11-24 15:06:00','Entrada por reabastecimiento #60',NULL,60),
(22,7,NULL,-5,'SALIDA','2025-11-24 15:15:44','Asignación a producto canjeable: Cerveza Aguila',NULL,NULL),
(23,1,19,23,'entrada','2025-11-29 23:25:07','Recepción de reabastecimiento #61',NULL,NULL),
(24,10,20,89,'entrada','2025-11-30 02:52:22','Entrada por reabastecimiento #80',NULL,80);
/*!40000 ALTER TABLE `movimiento_inventario` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `pago`
--

DROP TABLE IF EXISTS `pago`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `pago` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `venta_id` int(11) NOT NULL,
  `monto` decimal(12,2) NOT NULL,
  `metodo_pago` varchar(25) NOT NULL,
  `fecha_pago` datetime NOT NULL DEFAULT current_timestamp(),
  `estado` varchar(20) NOT NULL DEFAULT 'completado' COMMENT 'Posibles: completado, fallido, reembolsado',
  `referencia_transaccion` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `venta_id` (`venta_id`),
  CONSTRAINT `fk_pago_venta` FOREIGN KEY (`venta_id`) REFERENCES `venta` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pago`
--

LOCK TABLES `pago` WRITE;
/*!40000 ALTER TABLE `pago` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `pago` VALUES
(1,1,7600.00,'Efectivo','2025-09-02 10:00:00','completado',NULL),
(2,2,9500.00,'Tarjeta','2025-09-03 11:30:00','completado',NULL),
(3,3,4500.00,'Efectivo','2025-11-05 12:24:54','completado',NULL),
(4,4,54000.00,'Efectivo','2025-11-05 12:25:24','completado',NULL),
(5,5,45600.00,'Efectivo','2025-11-05 12:25:41','completado',NULL),
(6,6,4500.00,'Efectivo','2025-11-05 12:40:34','completado',NULL),
(7,7,22800.00,'Efectivo','2025-11-05 12:44:58','completado',NULL),
(8,8,25000.00,'Efectivo','2025-11-05 13:48:30','completado',NULL),
(9,9,18000.00,'Efectivo','2025-11-06 22:52:29','completado',NULL),
(17,17,3800.00,'efectivo','2025-11-22 05:34:57','completado',NULL),
(18,18,3000.00,'efectivo','2025-11-22 05:40:24','completado',NULL),
(19,19,3000.00,'efectivo','2025-11-22 05:40:34','completado',NULL),
(20,20,3000.00,'efectivo','2025-11-22 05:40:34','completado',NULL),
(21,21,3000.00,'efectivo','2025-11-22 05:40:34','completado',NULL),
(22,22,304700.00,'efectivo','2025-11-22 06:15:41','completado',NULL),
(23,23,54000.00,'efectivo','2025-11-22 06:26:10','completado',NULL),
(24,24,54000.00,'efectivo','2025-11-22 06:27:01','completado',NULL),
(25,25,54000.00,'efectivo','2025-11-22 06:28:05','completado',NULL),
(26,26,304700.00,'efectivo','2025-11-22 06:32:54','completado',NULL),
(27,27,9500.00,'efectivo','2025-11-23 06:02:59','completado',NULL),
(28,28,95000.00,'efectivo','2025-11-23 06:05:55','completado',NULL);
/*!40000 ALTER TABLE `pago` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `pedido`
--

DROP TABLE IF EXISTS `pedido`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `pedido` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cliente_id` bigint(20) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `fecha_pedido` datetime NOT NULL DEFAULT current_timestamp(),
  `estado` varchar(20) NOT NULL DEFAULT 'pendiente' COMMENT 'Posibles estados: pendiente, en_proceso, completado, cancelado',
  `total_pedido` decimal(12,2) NOT NULL DEFAULT 0.00,
  `observaciones` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `cliente_id` (`cliente_id`),
  KEY `usuario_id` (`usuario_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pedido`
--

LOCK TABLES `pedido` WRITE;
/*!40000 ALTER TABLE `pedido` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `pedido` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `pedido_detalle`
--

DROP TABLE IF EXISTS `pedido_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `pedido_detalle` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pedido_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `cantidad` int(11) NOT NULL,
  `precio_unitario` decimal(12,2) NOT NULL COMMENT 'Precio del producto en el momento del pedido',
  `subtotal` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `pedido_id` (`pedido_id`),
  KEY `producto_id` (`producto_id`),
  CONSTRAINT `fk_pedido_detalle_pedido` FOREIGN KEY (`pedido_id`) REFERENCES `pedido` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_pedido_detalle_producto` FOREIGN KEY (`producto_id`) REFERENCES `producto` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pedido_detalle`
--

LOCK TABLES `pedido_detalle` WRITE;
/*!40000 ALTER TABLE `pedido_detalle` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `pedido_detalle` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `pqrs`
--

DROP TABLE IF EXISTS `pqrs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `pqrs` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tipo` varchar(20) NOT NULL,
  `descripcion` text NOT NULL,
  `respuesta` text DEFAULT NULL,
  `estado` varchar(20) DEFAULT 'pendiente',
  `fecha_creacion` datetime NOT NULL DEFAULT current_timestamp(),
  `fecha_actualizacion` datetime DEFAULT NULL ON UPDATE current_timestamp(),
  `cliente_id` bigint(20) NOT NULL,
  `usuario_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `cliente_id` (`cliente_id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `fk_pqrs_cliente` FOREIGN KEY (`cliente_id`) REFERENCES `cliente` (`id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_pqrs_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pqrs`
--

LOCK TABLES `pqrs` WRITE;
/*!40000 ALTER TABLE `pqrs` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `pqrs` VALUES
(1,'SUGERENCIA','Más productos saludables',NULL,'en_proceso','2025-07-01 10:00:00',NULL,1,2),
(2,'peticion','Nuevo producto Amper de mango.','Se hara una solicitud de compra del producto solicitado','nuevo','2025-11-24 02:09:13','2025-11-24 02:22:25',5,4);
/*!40000 ALTER TABLE `pqrs` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `pqrs_evento`
--

DROP TABLE IF EXISTS `pqrs_evento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `pqrs_evento` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tipo_evento` varchar(20) NOT NULL,
  `comentario` longtext DEFAULT NULL,
  `fecha_evento` datetime(6) NOT NULL,
  `pqrs_id` bigint(20) NOT NULL,
  `usuario_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `pqrs_evento_pqrs_id_49150e1b_fk_pqrs_id` (`pqrs_id`),
  KEY `pqrs_evento_usuario_id_56d2eecd_fk_usuario_id` (`usuario_id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pqrs_evento`
--

LOCK TABLES `pqrs_evento` WRITE;
/*!40000 ALTER TABLE `pqrs_evento` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `pqrs_evento` VALUES
(2,'respuesta','Se hara una solicitud de compra del producto solicitado','2025-11-24 02:12:38.651102',2,4),
(3,'respuesta','Se hara una solicitud de compra del producto solicitado','2025-11-24 02:12:49.195214',2,4),
(4,'respuesta','Se hara una solicitud de compra del producto solicitado','2025-11-24 02:22:25.937688',2,4);
/*!40000 ALTER TABLE `pqrs_evento` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `producto`
--

DROP TABLE IF EXISTS `producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `producto` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `precio_unitario` decimal(12,2) NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `stock_minimo` int(11) NOT NULL DEFAULT 10,
  `categoria_id` int(11) NOT NULL,
  `stock_actual` int(10) unsigned NOT NULL,
  `costo_promedio` decimal(12,2) NOT NULL,
  `tasa_iva_id` int(11) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_producto_nombre` (`nombre`),
  KEY `categoria_id` (`categoria_id`),
  KEY `fk_producto_tasa_iva` (`tasa_iva_id`),
  CONSTRAINT `fk_producto_categoria` FOREIGN KEY (`categoria_id`) REFERENCES `categoria` (`id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_producto_tasa_iva` FOREIGN KEY (`tasa_iva_id`) REFERENCES `tasa_iva` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `producto`
--

LOCK TABLES `producto` WRITE;
/*!40000 ALTER TABLE `producto` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `producto` VALUES
(1,'Leche Entera 1L',3800.00,'Leche pasteurizada',10,1,23,3800.00,1),
(2,'Queso Campesino 500g',9500.00,'Queso fresco de vaca',5,2,48,7000.00,1),
(3,'Yogurt',3000.00,NULL,10,1,199,3000.00,1),
(4,'Manzana Postobon 1L',4500.00,'Sabor a manzana, 1L',3,4,0,0.00,1),
(7,'Cerveza Aguila',4500.00,'Tipo lager',1,3,323,4500.00,1),
(8,'Papas Fritas',2500.00,'Paquete de papas',5,5,0,0.00,1),
(9,'Poker',3000.00,NULL,10,3,121,3000.00,1),
(10,'Coronita',5000.00,NULL,5,3,89,5000.00,1),
(11,'Aguila 330 ml',3000.00,'Cerveza Lager',2,3,16,3000.00,1),
(12,'todo rico natural',3500.00,'paquete de papas surtido',2,6,43,3500.00,1),
(13,'Yogurt alpina',2500.00,NULL,12,1,0,0.00,1);
/*!40000 ALTER TABLE `producto` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `producto_canjeble`
--

DROP TABLE IF EXISTS `producto_canjeble`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `producto_canjeble` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` longtext DEFAULT NULL,
  `puntos_requeridos` decimal(10,2) NOT NULL,
  `stock_disponible` int(10) unsigned NOT NULL CHECK (`stock_disponible` >= 0),
  `activo` tinyint(1) NOT NULL,
  `fecha_creacion` datetime(6) NOT NULL,
  `producto_inventario_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `producto_canjeble`
--

LOCK TABLES `producto_canjeble` WRITE;
/*!40000 ALTER TABLE `producto_canjeble` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `producto_canjeble` VALUES
(1,'taza la playita ','',3.69,4,1,'2025-11-22 06:14:44.582337',NULL),
(2,'desodorante ','',10.00,2,1,'2025-11-23 06:04:58.215270',NULL),
(3,'Cerveza Aguila','Tipo lager',3.00,5,1,'2025-11-24 15:15:44.228844',7);
/*!40000 ALTER TABLE `producto_canjeble` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `proveedor`
--

DROP TABLE IF EXISTS `proveedor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `proveedor` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `documento_identificacion` varchar(20) DEFAULT NULL,
  `nombre_empresa` varchar(100) NOT NULL,
  `telefono` varchar(50) NOT NULL,
  `correo` varchar(50) NOT NULL,
  `direccion` varchar(255) NOT NULL,
  `tipo_documento` varchar(3) NOT NULL DEFAULT 'NIT',
  PRIMARY KEY (`id`),
  UNIQUE KEY `nit` (`documento_identificacion`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `proveedor`
--

LOCK TABLES `proveedor` WRITE;
/*!40000 ALTER TABLE `proveedor` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `proveedor` VALUES
(1,'800.123.456-7','Proveedor de Lacteos S.A.','123456789','contacto@lacteos.com','Calle Falsa 123','NIT'),
(2,'890.903.635-1','Postobon S.A.','3573612371','postobon@gmail.com','kra93 #32-13','NIT'),
(3,'860.005.224-6','Bavaria S.A.','2131456','lizarazojuanandres@gmail.com','cra105 #21-65','NIT'),
(4,'800.22 margarita-9','Papas Margarita','235156023','margaritas@gmail.com','cra100 #95-54','NIT'),
(5,'2032032','Fritolay','2342343243','fritolay@gmail.com','carrera 14 #12-32','NIT');
/*!40000 ALTER TABLE `proveedor` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `puntos_fidelizacion`
--

DROP TABLE IF EXISTS `puntos_fidelizacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `puntos_fidelizacion` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tipo` varchar(20) NOT NULL,
  `puntos` decimal(10,2) NOT NULL,
  `descripcion` varchar(255) NOT NULL,
  `fecha_transaccion` datetime(6) NOT NULL,
  `venta_id` int(11) DEFAULT NULL,
  `canje_id` bigint(20) DEFAULT NULL,
  `cliente_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `puntos_fidelizacion`
--

LOCK TABLES `puntos_fidelizacion` WRITE;
/*!40000 ALTER TABLE `puntos_fidelizacion` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `puntos_fidelizacion` VALUES
(1,'ganancia',0.79,'Compra de $9500 - Venta #27','2025-11-23 06:02:59.807102',27,NULL,3),
(2,'ganancia',7.92,'Compra de $95000 - Venta #28','2025-11-23 06:05:55.951945',28,NULL,3),
(3,'canje',-3.69,'Canje de taza la playita  (Web)','2025-11-23 06:38:15.186936',NULL,1,6),
(4,'canje',-3.69,'Canje de taza la playita  (Web)','2025-11-23 06:39:42.103931',NULL,2,6),
(5,'canje',-3.69,'Canje de taza la playita  (Web)','2025-11-24 15:15:13.806149',NULL,3,3);
/*!40000 ALTER TABLE `puntos_fidelizacion` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `reabastecimiento`
--

DROP TABLE IF EXISTS `reabastecimiento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `reabastecimiento` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fecha` datetime NOT NULL,
  `costo_total` decimal(12,2) NOT NULL,
  `estado` varchar(20) NOT NULL DEFAULT 'solicitado' COMMENT 'Posibles: solicitado, cancelado, recibido',
  `forma_pago` varchar(25) DEFAULT 'Efectivo',
  `observaciones` text DEFAULT NULL,
  `proveedor_id` int(11) NOT NULL,
  `iva` decimal(12,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`id`),
  KEY `proveedor_id` (`proveedor_id`),
  CONSTRAINT `fk_reabastecimiento_proveedor` FOREIGN KEY (`proveedor_id`) REFERENCES `proveedor` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=81 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reabastecimiento`
--

LOCK TABLES `reabastecimiento` WRITE;
/*!40000 ALTER TABLE `reabastecimiento` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `reabastecimiento` VALUES
(1,'2025-09-01 09:00:00',670000.00,'recibido','Efectivo','Reabastecimiento inicial',1,0.00),
(36,'2025-11-05 11:38:27',270000.00,'recibido','pse','',3,0.00),
(37,'2025-11-05 13:45:25',25000.00,'recibido','pse','',4,0.00),
(38,'2025-11-06 22:53:32',450000.00,'recibido','pse','',3,0.00),
(40,'2025-11-06 22:54:41',900000.00,'recibido','pse','',3,0.00),
(45,'2025-11-11 20:03:03',19000.00,'recibido','efectivo','',3,0.00),
(46,'2025-11-13 23:34:09',297000.00,'recibido','consignacion','',3,0.00),
(55,'2025-11-19 13:20:16',600000.00,'recibido','pse','',3,0.00),
(58,'2025-11-21 11:50:36',165000.00,'recibido','efectivo','',3,0.00),
(59,'2025-11-21 12:09:50',150500.00,'recibido','efectivo','',5,0.00),
(60,'2025-11-24 15:05:34',69000.00,'recibido','pse','',3,0.00),
(61,'2025-11-24 15:16:31',87400.00,'recibido','tarjeta_credito','',4,0.00),
(62,'2025-11-29 23:36:59',300000.00,'solicitado','efectivo','',3,57000.00),
(63,'2025-11-29 23:59:37',150000.00,'solicitado','efectivo','',3,28500.00),
(64,'2025-11-30 01:30:34',243000.00,'solicitado','efectivo','',3,46170.00),
(75,'2025-11-30 02:11:21',192000.00,'solicitado','efectivo','',3,36480.00),
(78,'2025-11-30 02:21:40',450000.00,'solicitado','efectivo','',3,85500.00),
(80,'2025-11-30 02:36:17',450000.00,'recibido','efectivo','',3,85500.00);
/*!40000 ALTER TABLE `reabastecimiento` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `reabastecimiento_detalle`
--

DROP TABLE IF EXISTS `reabastecimiento_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `reabastecimiento_detalle` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `reabastecimiento_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `cantidad` int(11) NOT NULL,
  `costo_unitario` decimal(12,2) NOT NULL,
  `fecha_caducidad` date DEFAULT NULL,
  `cantidad_recibida` int(11) NOT NULL,
  `iva` decimal(12,2) NOT NULL DEFAULT 0.00,
  `recibido_por_id` bigint(20) DEFAULT NULL,
  `fecha_recepcion` datetime DEFAULT NULL,
  `cantidad_anterior` int(11) DEFAULT 0,
  `numero_lote` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `reabastecimiento_id` (`reabastecimiento_id`),
  KEY `producto_id` (`producto_id`),
  KEY `fk_recibido_por` (`recibido_por_id`),
  CONSTRAINT `fk_reabastecimiento_detalle_reabastecimiento` FOREIGN KEY (`reabastecimiento_id`) REFERENCES `reabastecimiento` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_recibido_por` FOREIGN KEY (`recibido_por_id`) REFERENCES `usuario` (`id`) ON DELETE SET NULL,
  CONSTRAINT `reabastecimiento_detalle_producto_id_63c5cefe_fk_producto_id` FOREIGN KEY (`producto_id`) REFERENCES `producto` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=81 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reabastecimiento_detalle`
--

LOCK TABLES `reabastecimiento_detalle` WRITE;
/*!40000 ALTER TABLE `reabastecimiento_detalle` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `reabastecimiento_detalle` VALUES
(1,1,1,100,2500.00,NULL,100,0.00,NULL,NULL,0,NULL),
(2,1,2,60,7000.00,NULL,60,0.00,NULL,NULL,0,NULL),
(38,36,7,60,4500.00,'2025-12-31',60,0.00,NULL,NULL,0,NULL),
(39,37,8,10,2500.00,'2025-12-06',10,0.00,NULL,NULL,0,NULL),
(40,38,7,100,4500.00,'2026-01-17',100,0.00,NULL,NULL,0,NULL),
(42,40,7,200,4500.00,'2026-01-15',199,0.00,NULL,NULL,0,NULL),
(45,45,1,5,3800.00,'2026-01-10',5,0.00,NULL,NULL,0,NULL),
(46,46,9,99,3000.00,'2026-02-12',99,0.00,NULL,NULL,0,NULL),
(55,55,3,200,3000.00,'2026-01-03',199,0.00,NULL,NULL,0,NULL),
(58,58,11,55,3000.00,'2025-11-29',55,0.00,NULL,NULL,0,NULL),
(59,59,12,43,3500.00,'2025-11-29',43,0.00,NULL,NULL,0,NULL),
(60,60,9,23,3000.00,'2026-01-01',22,0.00,NULL,NULL,0,NULL),
(61,61,1,23,3800.00,'2025-12-31',23,0.00,NULL,'2025-11-29 23:50:01',0,'R61-P1-61'),
(62,62,10,60,5000.00,'2026-01-24',0,0.00,NULL,NULL,0,NULL),
(63,63,10,30,5000.00,'2025-12-31',0,0.00,NULL,NULL,0,NULL),
(64,64,10,54,4500.00,'2026-01-06',0,0.00,NULL,NULL,0,NULL),
(75,75,9,64,3000.00,'2025-12-31',0,0.00,NULL,NULL,0,NULL),
(78,78,10,90,5000.00,'2026-01-08',0,0.00,NULL,NULL,0,NULL),
(80,80,10,90,5000.00,'2026-01-01',89,0.00,4,'2025-11-30 02:52:22',0,NULL);
/*!40000 ALTER TABLE `reabastecimiento_detalle` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `rol`
--

DROP TABLE IF EXISTS `rol`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `rol` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(35) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rol`
--

LOCK TABLES `rol` WRITE;
/*!40000 ALTER TABLE `rol` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `rol` VALUES
(1,'Administrador'),
(2,'Vendedor');
/*!40000 ALTER TABLE `rol` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `tasa_iva`
--

DROP TABLE IF EXISTS `tasa_iva`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tasa_iva` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `porcentaje` decimal(5,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tasa_iva`
--

LOCK TABLES `tasa_iva` WRITE;
/*!40000 ALTER TABLE `tasa_iva` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `tasa_iva` VALUES
(1,'IVA General 19%',19.00),
(2,'IVA Reducido 5%',5.00),
(3,'Exento 0%',0.00);
/*!40000 ALTER TABLE `tasa_iva` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `usuario`
--

DROP TABLE IF EXISTS `usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `documento` varchar(20) NOT NULL,
  `nombres` varchar(50) NOT NULL,
  `apellidos` varchar(50) NOT NULL,
  `correo` varchar(60) NOT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `contrasena` varchar(255) NOT NULL,
  `estado` varchar(20) NOT NULL,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `ultimo_login` timestamp NULL DEFAULT NULL,
  `rol_id` int(11) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_superuser` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `documento` (`documento`),
  UNIQUE KEY `correo` (`correo`),
  KEY `rol_id` (`rol_id`),
  CONSTRAINT `fk_usuario_rol` FOREIGN KEY (`rol_id`) REFERENCES `rol` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuario`
--

LOCK TABLES `usuario` WRITE;
/*!40000 ALTER TABLE `usuario` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `usuario` VALUES
(1,'1014477103','Juan','Lizarazo','juan.vendedor@laplayita.com','3105416287','hash_contrasena_vendedor','activo','2025-10-10 22:48:22',NULL,2,0,0),
(2,'1234567','Admin','Principal','admin@laplayita.com','32124551','hash_contrasena_admin','activo','2025-10-10 22:48:22','2025-11-09 07:03:56',1,0,0),
(4,'10000000','Laura','Gomez','laura.admin@laplayita.com',NULL,'pbkdf2_sha256$1000000$5IUYpFqgilB2EvaR9GQJya$hH7HV5VkSrpqZSxNsg5r9+/o+2BQyzYwWbPiyTDV204=','activo','2025-10-13 19:08:10','2025-11-30 06:48:22',1,0,0),
(5,'1014477104','Juan Andres','Lizarazo Capera','lizarazojuanandres@gmail.com','3105416287','pbkdf2_sha256$1000000$UFwj2ILaUlQL994XzKPWC9$KMJ5lGcAoz0n/JkjQsMt3/WVQ9ZH96GT9UowK868yaU=','activo','2025-11-13 05:28:21','2025-11-13 06:23:15',2,0,0),
(6,'1000','Test','Admin','test@admin.com',NULL,'pbkdf2_sha256$1000000$wQDpWFuo6WGjhOXadQOugV$GO7IdMPoLIASNGTmuZthpsgeg0W+QFFnFPa3Hqfupjs=','activo','2025-11-22 10:36:02','2025-11-22 10:37:26',1,1,1);
/*!40000 ALTER TABLE `usuario` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `usuario_groups`
--

DROP TABLE IF EXISTS `usuario_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario_groups` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `usuario_id` bigint(20) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `usuario_groups_usuario_id_group_id` (`usuario_id`,`group_id`),
  KEY `usuario_groups_usuario_id` (`usuario_id`),
  KEY `usuario_groups_group_id` (`group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuario_groups`
--

LOCK TABLES `usuario_groups` WRITE;
/*!40000 ALTER TABLE `usuario_groups` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `usuario_groups` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `usuario_user_permissions`
--

DROP TABLE IF EXISTS `usuario_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario_user_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `usuario_id` bigint(20) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `usuario_user_permissions_usuario_id_permission_id` (`usuario_id`,`permission_id`),
  KEY `usuario_user_permissions_usuario_id` (`usuario_id`),
  KEY `usuario_user_permissions_permission_id` (`permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuario_user_permissions`
--

LOCK TABLES `usuario_user_permissions` WRITE;
/*!40000 ALTER TABLE `usuario_user_permissions` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `usuario_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `venta`
--

DROP TABLE IF EXISTS `venta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `venta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fecha_venta` datetime NOT NULL,
  `canal_venta` varchar(20) NOT NULL DEFAULT 'Tienda',
  `cliente_id` bigint(20) NOT NULL,
  `usuario_id` bigint(20) NOT NULL,
  `pedido_id` int(11) DEFAULT NULL COMMENT 'Vincula la venta a un pedido original',
  `total_venta` decimal(12,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`id`),
  KEY `cliente_id` (`cliente_id`),
  KEY `usuario_id` (`usuario_id`),
  KEY `pedido_id` (`pedido_id`),
  CONSTRAINT `fk_venta_pedido` FOREIGN KEY (`pedido_id`) REFERENCES `pedido` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_venta_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `venta`
--

LOCK TABLES `venta` WRITE;
/*!40000 ALTER TABLE `venta` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `venta` VALUES
(1,'2025-09-02 10:00:00','Tienda',1,1,NULL,7600.00),
(2,'2025-09-03 11:30:00','Domicilio',2,1,NULL,9500.00),
(3,'2025-11-05 12:24:54','local',1,4,NULL,4500.00),
(4,'2025-11-05 12:25:24','local',1,4,NULL,54000.00),
(5,'2025-11-05 12:25:41','local',2,4,NULL,45600.00),
(6,'2025-11-05 12:40:34','local',2,4,NULL,4500.00),
(7,'2025-11-05 12:44:58','local',1,4,NULL,22800.00),
(8,'2025-11-05 13:48:30','local',2,4,NULL,25000.00),
(9,'2025-11-06 22:52:29','local',2,4,NULL,18000.00),
(17,'2025-11-22 05:34:57','mostrador',5,4,NULL,3800.00),
(18,'2025-11-22 05:40:24','mostrador',1,6,NULL,3000.00),
(19,'2025-11-22 05:40:34','mostrador',3,6,NULL,3000.00),
(20,'2025-11-22 05:40:34','mostrador',3,6,NULL,3000.00),
(21,'2025-11-22 05:40:34','mostrador',3,6,NULL,3000.00),
(22,'2025-11-22 06:15:41','mostrador',3,6,NULL,304700.00),
(23,'2025-11-22 06:26:10','mostrador',3,4,NULL,54000.00),
(24,'2025-11-22 06:27:01','mostrador',3,4,NULL,54000.00),
(25,'2025-11-22 06:28:05','mostrador',3,4,NULL,54000.00),
(26,'2025-11-22 06:32:54','mostrador',3,6,NULL,304700.00),
(27,'2025-11-23 06:02:59','mostrador',3,4,NULL,9500.00),
(28,'2025-11-23 06:05:55','mostrador',3,4,NULL,95000.00);
/*!40000 ALTER TABLE `venta` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `venta_detalle`
--

DROP TABLE IF EXISTS `venta_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `venta_detalle` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `venta_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `lote_id` int(11) NOT NULL,
  `cantidad` int(11) NOT NULL,
  `subtotal` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `venta_id` (`venta_id`),
  KEY `producto_id` (`producto_id`),
  KEY `lote_id` (`lote_id`),
  CONSTRAINT `fk_venta_detalle_lote` FOREIGN KEY (`lote_id`) REFERENCES `lote` (`id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_venta_detalle_producto` FOREIGN KEY (`producto_id`) REFERENCES `producto` (`id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_venta_detalle_venta` FOREIGN KEY (`venta_id`) REFERENCES `venta` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `venta_detalle`
--

LOCK TABLES `venta_detalle` WRITE;
/*!40000 ALTER TABLE `venta_detalle` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `venta_detalle` VALUES
(1,1,1,1,2,7600.00),
(2,2,2,2,1,9500.00),
(3,3,7,3,1,4500.00),
(4,4,7,3,12,54000.00),
(5,5,1,1,12,45600.00),
(6,6,7,3,1,4500.00),
(7,7,1,1,6,22800.00),
(8,8,8,4,10,25000.00),
(9,9,7,3,4,18000.00),
(17,17,1,1,1,3800.00),
(18,18,11,14,1,3000.00),
(19,19,11,14,1,3000.00),
(20,20,11,14,1,3000.00),
(21,21,11,14,1,3000.00),
(22,22,1,1,79,300200.00),
(23,22,7,3,1,4500.00),
(24,23,7,3,12,54000.00),
(25,24,11,14,18,54000.00),
(26,25,11,14,18,54000.00),
(27,27,2,2,1,9500.00),
(28,28,2,2,10,95000.00);
/*!40000 ALTER TABLE `venta_detalle` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Temporary table structure for view `vw_inventario_actual_producto`
--

DROP TABLE IF EXISTS `vw_inventario_actual_producto`;
/*!50001 DROP VIEW IF EXISTS `vw_inventario_actual_producto`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `vw_inventario_actual_producto` AS SELECT
 1 AS `producto_id`,
  1 AS `producto_nombre`,
  1 AS `stock_actual`,
  1 AS `costo_promedio`,
  1 AS `stock_calculado_lotes`,
  1 AS `numero_lotes_activos` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `vw_movimientos_recientes`
--

DROP TABLE IF EXISTS `vw_movimientos_recientes`;
/*!50001 DROP VIEW IF EXISTS `vw_movimientos_recientes`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `vw_movimientos_recientes` AS SELECT
 1 AS `movimiento_id`,
  1 AS `fecha_movimiento`,
  1 AS `tipo_movimiento`,
  1 AS `cantidad`,
  1 AS `producto_id`,
  1 AS `producto_nombre`,
  1 AS `numero_lote`,
  1 AS `descripcion`,
  1 AS `venta_id`,
  1 AS `reabastecimiento_id` */;
SET character_set_client = @saved_cs_client;

--
-- Dumping events for database 'laplayita'
--

--
-- Dumping routines for database 'laplayita'
--
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_add_stock` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_uca1400_ai_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_add_stock`(
  IN p_reabastecimiento_detalle_id INT,
  IN p_producto_id INT,
  IN p_numero_lote VARCHAR(100),
  IN p_cantidad INT,
  IN p_costo_unitario DECIMAL(12,2),
  IN p_fecha_caducidad DATE,
  IN p_reabastecimiento_id INT,
  IN p_descripcion VARCHAR(255)
)
BEGIN
  DECLARE v_lote_id INT;

  START TRANSACTION;
    INSERT INTO lote (producto_id, reabastecimiento_detalle_id, numero_lote, cantidad_disponible, costo_unitario_lote, fecha_caducidad)
    VALUES (p_producto_id, p_reabastecimiento_detalle_id, p_numero_lote, p_cantidad, p_costo_unitario, p_fecha_caducidad);

    SET v_lote_id = LAST_INSERT_ID();

    INSERT INTO movimiento_inventario (producto_id, lote_id, cantidad, tipo_movimiento, descripcion, reabastecimiento_id)
    VALUES (p_producto_id, v_lote_id, p_cantidad, 'ENTRADA', p_descripcion, p_reabastecimiento_id);

  COMMIT;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_recalcular_costo_promedio_por_producto` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_uca1400_ai_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_recalcular_costo_promedio_por_producto`(IN p_producto_id INT)
BEGIN
  DECLARE total_cantidad INT DEFAULT 0;
  DECLARE total_valor DECIMAL(18,4) DEFAULT 0.00;

  SELECT COALESCE(SUM(cantidad_disponible),0), COALESCE(SUM(cantidad_disponible * costo_unitario_lote),0)
  INTO total_cantidad, total_valor
  FROM lote
  WHERE producto_id = p_producto_id;

  IF total_cantidad = 0 THEN
    UPDATE producto SET costo_promedio = 0.00 WHERE id = p_producto_id;
  ELSE
    UPDATE producto SET costo_promedio = ROUND(total_valor / total_cantidad,2) WHERE id = p_producto_id;
  END IF;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_sell_stock` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_uca1400_ai_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_sell_stock`(
  IN p_venta_id INT,
  IN p_producto_id INT,
  IN p_lote_id INT,
  IN p_cantidad INT,
  IN p_descripcion VARCHAR(255)
)
BEGIN
  DECLARE v_actual INT;

  START TRANSACTION;
    SELECT cantidad_disponible INTO v_actual FROM lote WHERE id = p_lote_id FOR UPDATE;
    IF v_actual IS NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Lote no existe';
    END IF;

    IF v_actual < p_cantidad THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Stock insuficiente en lote';
    END IF;

    UPDATE lote SET cantidad_disponible = cantidad_disponible - p_cantidad WHERE id = p_lote_id;

    INSERT INTO movimiento_inventario (producto_id, lote_id, cantidad, tipo_movimiento, descripcion, venta_id)
    VALUES (p_producto_id, p_lote_id, -p_cantidad, 'SALIDA', p_descripcion, p_venta_id);

  COMMIT;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Current Database: `laplayita`
--

USE `laplayita`;

--
-- Final view structure for view `vw_inventario_actual_producto`
--

/*!50001 DROP VIEW IF EXISTS `vw_inventario_actual_producto`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_uca1400_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_inventario_actual_producto` AS select `p`.`id` AS `producto_id`,`p`.`nombre` AS `producto_nombre`,`p`.`stock_actual` AS `stock_actual`,`p`.`costo_promedio` AS `costo_promedio`,coalesce(sum(`l`.`cantidad_disponible`),0) AS `stock_calculado_lotes`,count(`l`.`id`) AS `numero_lotes_activos` from (`producto` `p` left join `lote` `l` on(`p`.`id` = `l`.`producto_id`)) group by `p`.`id`,`p`.`nombre`,`p`.`stock_actual`,`p`.`costo_promedio` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_movimientos_recientes`
--

/*!50001 DROP VIEW IF EXISTS `vw_movimientos_recientes`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_uca1400_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_movimientos_recientes` AS select `mi`.`id` AS `movimiento_id`,`mi`.`fecha_movimiento` AS `fecha_movimiento`,`mi`.`tipo_movimiento` AS `tipo_movimiento`,`mi`.`cantidad` AS `cantidad`,`p`.`id` AS `producto_id`,`p`.`nombre` AS `producto_nombre`,`l`.`numero_lote` AS `numero_lote`,`mi`.`descripcion` AS `descripcion`,`mi`.`venta_id` AS `venta_id`,`mi`.`reabastecimiento_id` AS `reabastecimiento_id` from ((`movimiento_inventario` `mi` join `producto` `p` on(`mi`.`producto_id` = `p`.`id`)) left join `lote` `l` on(`mi`.`lote_id` = `l`.`id`)) order by `mi`.`fecha_movimiento` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2025-11-29 22:11:49
