CREATE DATABASE IF NOT EXISTS control_gastos_db;
USE control_gastos_db;

-- Tabla de Categorías de Gastos
CREATE TABLE IF NOT EXISTS categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(150)
);

-- Tabla de Registro de Gastos
DROP TABLE IF EXISTS gastos;

CREATE TABLE gastos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    concepto VARCHAR(100) NOT NULL,
    monto DECIMAL(10, 2) NOT NULL,
    fecha DATE NOT NULL,
    categoria_id INT NOT NULL,
    dias_detalle TEXT NULL,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE
);

-- Inserción de categorías típicas para universitarios
INSERT IGNORE INTO categorias (id, nombre, descripcion) VALUES
(1, 'Alimentación', 'Comidas, refrigerios y cafetería'),
(2, 'Transporte', 'Buses, taxis, combustible'),
(3, 'Materiales de Estudio', 'Copias, libros, papelería'),
(4, 'Vivienda / Servicios', 'Renta, internet, luz, agua'),
(5, 'Ocio y Recreación', 'Salidas, entretenimiento');

SELECT g.id, g.concepto, g.monto, g.fecha, c.nombre AS categoria
FROM control_gastos_db.gastos g
INNER JOIN control_gastos_db.categorias c ON g.categoria_id = c.id;