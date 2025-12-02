-- Trigger para generar número de caso automáticamente
-- Ejecutar después de la migración principal

USE laplayita;

DROP TRIGGER IF EXISTS before_insert_pqrs;

DELIMITER $$

CREATE TRIGGER before_insert_pqrs
BEFORE INSERT ON pqrs
FOR EACH ROW
BEGIN
    DECLARE contador INT;
    DECLARE anio INT;
    
    IF NEW.numero_caso IS NULL OR NEW.numero_caso = '' THEN
        SET anio = YEAR(NOW());
        
        SELECT COUNT(*) + 1 INTO contador
        FROM pqrs
        WHERE YEAR(fecha_creacion) = anio;
        
        SET NEW.numero_caso = CONCAT('PQRS-', anio, '-', LPAD(contador, 4, '0'));
    END IF;
END$$

DELIMITER ;
