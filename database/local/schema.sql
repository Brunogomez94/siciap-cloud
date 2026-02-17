-- =============================================================================
-- SICIAP CLOUD - Esquema de Base de Datos Local (PostgreSQL)
-- Versión: 1.0
-- Descripción: Esquema completo para procesamiento ETL local
-- =============================================================================

-- Crear esquema principal
CREATE SCHEMA IF NOT EXISTS siciap;

-- =============================================================================
-- TABLA: ordenes
-- Descripción: Órdenes de compra y sus estados
-- =============================================================================
CREATE TABLE IF NOT EXISTS siciap.ordenes (
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

CREATE INDEX IF NOT EXISTS idx_ordenes_id_llamado ON siciap.ordenes(id_llamado);
CREATE INDEX IF NOT EXISTS idx_ordenes_codigo ON siciap.ordenes(codigo);
CREATE INDEX IF NOT EXISTS idx_ordenes_estado ON siciap.ordenes(estado);

-- =============================================================================
-- TABLA: ejecucion
-- Descripción: Ejecución de contratos por ítem
-- =============================================================================
CREATE TABLE IF NOT EXISTS siciap.ejecucion (
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

CREATE INDEX IF NOT EXISTS idx_ejecucion_id_llamado ON siciap.ejecucion(id_llamado);
CREATE INDEX IF NOT EXISTS idx_ejecucion_codigo ON siciap.ejecucion(codigo);
CREATE INDEX IF NOT EXISTS idx_ejecucion_item ON siciap.ejecucion(item);

-- =============================================================================
-- TABLA: datosejecucion
-- Descripción: Datos generales de ejecución por llamado
-- =============================================================================
CREATE TABLE IF NOT EXISTS siciap.datosejecucion (
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

CREATE INDEX IF NOT EXISTS idx_datosejecucion_vigente ON siciap.datosejecucion(vigente);

-- =============================================================================
-- TABLA: stock_critico
-- Descripción: Stock crítico de productos
-- =============================================================================
CREATE TABLE IF NOT EXISTS siciap.stock_critico (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(255) NOT NULL UNIQUE,
    descripcion TEXT,
    stock_disponible NUMERIC(18,2) DEFAULT 0,
    stock_minimo NUMERIC(18,2) DEFAULT 0,
    dmp NUMERIC(18,2),  -- Días de medicamento pendiente
    estado VARCHAR(50),  -- 'critico', 'bajo', 'normal'
    ultima_actualizacion TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_stock_critico_codigo ON siciap.stock_critico(codigo);
CREATE INDEX IF NOT EXISTS idx_stock_critico_estado ON siciap.stock_critico(estado);

-- =============================================================================
-- TABLA: pedidos
-- Descripción: Pedidos pendientes
-- =============================================================================
CREATE TABLE IF NOT EXISTS siciap.pedidos (
    id SERIAL PRIMARY KEY,
    id_llamado INTEGER,
    codigo VARCHAR(255),
    item INTEGER,
    cantidad_solicitada NUMERIC(18,2),
    cantidad_pendiente NUMERIC(18,2),
    fecha_solicitud DATE,
    fecha_requerida DATE,
    estado VARCHAR(50),  -- 'pendiente', 'en_proceso', 'completado'
    observaciones TEXT,
    creado_en TIMESTAMPTZ DEFAULT now(),
    actualizado_en TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pedidos_id_llamado ON siciap.pedidos(id_llamado);
CREATE INDEX IF NOT EXISTS idx_pedidos_codigo ON siciap.pedidos(codigo);
CREATE INDEX IF NOT EXISTS idx_pedidos_estado ON siciap.pedidos(estado);

-- =============================================================================
-- TABLA: cantidad_solicitada
-- Descripción: Cantidad solicitada y fecha "Ver en fecha" por ítem
-- =============================================================================
CREATE TABLE IF NOT EXISTS siciap.cantidad_solicitada (
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
    ON siciap.cantidad_solicitada(emitir_en) 
    WHERE emitir_en IS NOT NULL;

-- =============================================================================
-- TABLA: recordatorios
-- Descripción: Recordatorios y alertas
-- =============================================================================
CREATE TABLE IF NOT EXISTS siciap.recordatorios (
    id SERIAL PRIMARY KEY,
    id_llamado INTEGER,
    licitacion VARCHAR(255),
    codigo VARCHAR(255),
    item INTEGER,
    fecha_recordatorio DATE NOT NULL,
    mensaje TEXT,
    creado_en TIMESTAMPTZ DEFAULT now(),
    notificado BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_recordatorios_fecha ON siciap.recordatorios(fecha_recordatorio);
CREATE INDEX IF NOT EXISTS idx_recordatorios_notificado ON siciap.recordatorios(notificado);

-- =============================================================================
-- TABLA: vencimientos_parques
-- Descripción: Vencimientos de productos en parques
-- =============================================================================
CREATE TABLE IF NOT EXISTS siciap.vencimientos_parques (
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

CREATE INDEX IF NOT EXISTS idx_vencimientos_codigo ON siciap.vencimientos_parques(codigo);
CREATE INDEX IF NOT EXISTS idx_vencimientos_fecha ON siciap.vencimientos_parques(fec_vencimiento);

-- =============================================================================
-- COMENTARIOS EN TABLAS
-- =============================================================================
COMMENT ON TABLE siciap.ordenes IS 'Órdenes de compra y sus estados';
COMMENT ON TABLE siciap.ejecucion IS 'Ejecución de contratos por ítem';
COMMENT ON TABLE siciap.datosejecucion IS 'Datos generales de ejecución por llamado';
COMMENT ON TABLE siciap.stock_critico IS 'Stock crítico de productos';
COMMENT ON TABLE siciap.pedidos IS 'Pedidos pendientes';
COMMENT ON TABLE siciap.cantidad_solicitada IS 'Cantidad solicitada y fecha "Ver en fecha" por ítem';
COMMENT ON TABLE siciap.recordatorios IS 'Recordatorios y alertas';
COMMENT ON TABLE siciap.vencimientos_parques IS 'Vencimientos de productos en parques';
