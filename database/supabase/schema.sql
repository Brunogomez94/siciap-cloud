-- =============================================================================
-- SICIAP CLOUD - Esquema para Supabase (Nube)
-- Versión: 1.0
-- Descripción: Esquema optimizado para visualización en Supabase
-- Nota: Este esquema contiene solo las tablas necesarias para visualización
--       Los datos se sincronizan desde la base de datos local
-- =============================================================================

-- Las tablas en Supabase son idénticas a las locales pero optimizadas para lectura
-- Se pueden agregar vistas materializadas y índices adicionales para mejor rendimiento

-- =============================================================================
-- TABLA: ordenes
-- =============================================================================
CREATE TABLE IF NOT EXISTS ordenes (
    id SERIAL PRIMARY KEY,
    id_llamado INTEGER NOT NULL,
    llamado VARCHAR(255),
    proveedor VARCHAR(255),
    codigo VARCHAR(255),
    item INTEGER,
    saldo NUMERIC(18,2),
    estado VARCHAR(100),
    fecha_orden DATE,
    fecha_vencimiento DATE,
    observaciones TEXT,
    creado_en TIMESTAMPTZ DEFAULT now(),
    actualizado_en TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ordenes_id_llamado ON ordenes(id_llamado);
CREATE INDEX IF NOT EXISTS idx_ordenes_codigo ON ordenes(codigo);
CREATE INDEX IF NOT EXISTS idx_ordenes_estado ON ordenes(estado);

-- =============================================================================
-- TABLA: ejecucion
-- =============================================================================
CREATE TABLE IF NOT EXISTS ejecucion (
    id SERIAL PRIMARY KEY,
    id_llamado INTEGER NOT NULL,
    licitacion VARCHAR(255) NOT NULL,
    codigo VARCHAR(255) NOT NULL,
    item INTEGER NOT NULL,
    cantidad_ejecutada NUMERIC(18,2) DEFAULT 0,
    precio_unitario NUMERIC(18,4),
    monto_total NUMERIC(18,2),
    fecha_ejecucion DATE,
    observaciones TEXT,
    creado_en TIMESTAMPTZ DEFAULT now(),
    actualizado_en TIMESTAMPTZ DEFAULT now(),
    UNIQUE(id_llamado, licitacion, codigo, item)
);

CREATE INDEX IF NOT EXISTS idx_ejecucion_id_llamado ON ejecucion(id_llamado);
CREATE INDEX IF NOT EXISTS idx_ejecucion_codigo ON ejecucion(codigo);

-- =============================================================================
-- TABLA: datosejecucion
-- =============================================================================
CREATE TABLE IF NOT EXISTS datosejecucion (
    id_llamado INTEGER PRIMARY KEY,
    llamado VARCHAR(255),
    descripcion_llamado TEXT,
    vigente BOOLEAN DEFAULT TRUE,
    dirigido_a TEXT,
    lugares TEXT,
    fecha_inicio DATE,
    fecha_fin DATE,
    monto_total NUMERIC(18,2),
    precio_unitario NUMERIC(18,4),
    observaciones TEXT,
    creado_en TIMESTAMPTZ DEFAULT now(),
    actualizado_en TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_datosejecucion_vigente ON datosejecucion(vigente);

-- =============================================================================
-- TABLA: stock_critico
-- =============================================================================
CREATE TABLE IF NOT EXISTS stock_critico (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(255) NOT NULL UNIQUE,
    descripcion TEXT,
    stock_disponible NUMERIC(18,2) DEFAULT 0,
    stock_minimo NUMERIC(18,2) DEFAULT 0,
    dmp NUMERIC(18,2),
    estado VARCHAR(50),
    ultima_actualizacion TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_stock_critico_codigo ON stock_critico(codigo);
CREATE INDEX IF NOT EXISTS idx_stock_critico_estado ON stock_critico(estado);

-- =============================================================================
-- TABLA: pedidos
-- =============================================================================
CREATE TABLE IF NOT EXISTS pedidos (
    id SERIAL PRIMARY KEY,
    id_llamado INTEGER,
    codigo VARCHAR(255),
    item INTEGER,
    cantidad_solicitada NUMERIC(18,2),
    cantidad_pendiente NUMERIC(18,2),
    fecha_solicitud DATE,
    fecha_requerida DATE,
    estado VARCHAR(50),
    observaciones TEXT,
    creado_en TIMESTAMPTZ DEFAULT now(),
    actualizado_en TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pedidos_id_llamado ON pedidos(id_llamado);
CREATE INDEX IF NOT EXISTS idx_pedidos_codigo ON pedidos(codigo);
CREATE INDEX IF NOT EXISTS idx_pedidos_estado ON pedidos(estado);

-- =============================================================================
-- TABLA: cantidad_solicitada
-- =============================================================================
CREATE TABLE IF NOT EXISTS cantidad_solicitada (
    id_llamado INTEGER NOT NULL,
    licitacion VARCHAR(255) NOT NULL,
    codigo VARCHAR(255) NOT NULL,
    item INTEGER NOT NULL,
    cantidad_solicitada NUMERIC(18,2) DEFAULT 0,
    emitir_en DATE,
    actualizado_en TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (id_llamado, licitacion, codigo, item)
);

CREATE INDEX IF NOT EXISTS idx_cantidad_solicitada_emitir_en 
    ON cantidad_solicitada(emitir_en) 
    WHERE emitir_en IS NOT NULL;

-- =============================================================================
-- TABLA: vencimientos_parques
-- Descripción: Vencimientos de productos en parques (fechas y semáforos)
-- =============================================================================
CREATE TABLE IF NOT EXISTS vencimientos_parques (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    fec_vencimiento DATE,
    stock_disponible NUMERIC(18,2) DEFAULT 0,
    parque VARCHAR(255),
    observaciones TEXT,
    creado_en TIMESTAMPTZ DEFAULT now(),
    actualizado_en TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_vencimientos_codigo ON vencimientos_parques(codigo);
CREATE INDEX IF NOT EXISTS idx_vencimientos_fecha ON vencimientos_parques(fec_vencimiento);

-- =============================================================================
-- VISTA MATERIALIZADA: vista_unificada
-- Descripción: Vista optimizada para dashboard con datos unificados
-- =============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS vista_unificada AS
SELECT 
    e.id_llamado,
    e.licitacion,
    e.codigo,
    e.item,
    COALESCE(e.precio_unitario, de.precio_unitario) as precio_unitario,
    e.cantidad_ejecutada,
    COALESCE(cs.cantidad_solicitada, 0) as cantidad_solicitada,
    cs.emitir_en,
    de.vigente,
    de.dirigido_a,
    de.lugares,
    de.descripcion_llamado,
    s.stock_disponible as stock_actual,
    s.estado as estado_stock,
    o.estado as estado_orden,
    o.saldo as saldo_orden,
    v.fec_vencimiento,
    v.stock_disponible as stock_vencimiento
FROM ejecucion e
LEFT JOIN datosejecucion de ON e.id_llamado = de.id_llamado
LEFT JOIN cantidad_solicitada cs 
    ON e.id_llamado = cs.id_llamado 
    AND e.licitacion = cs.licitacion 
    AND e.codigo = cs.codigo 
    AND e.item = cs.item
LEFT JOIN stock_critico s ON e.codigo = s.codigo
LEFT JOIN ordenes o 
    ON e.id_llamado = o.id_llamado 
    AND e.codigo = o.codigo
LEFT JOIN vencimientos_parques v ON e.codigo = v.codigo;

CREATE UNIQUE INDEX IF NOT EXISTS idx_vista_unificada_unique 
    ON vista_unificada(id_llamado, licitacion, codigo, item);

-- Función para refrescar la vista materializada
CREATE OR REPLACE FUNCTION refresh_vista_unificada()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY vista_unificada;
END;
$$ LANGUAGE plpgsql;
