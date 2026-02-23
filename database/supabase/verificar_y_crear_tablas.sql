-- =============================================================================
-- VERIFICAR Y CREAR TABLAS SI NO EXISTEN
-- Ejecuta este script si las tablas no aparecen después de ejecutar schema.sql
-- =============================================================================

-- Verificar qué tablas existen actualmente
SELECT 
    tablename,
    schemaname
FROM pg_catalog.pg_tables
WHERE schemaname = 'public'
  AND tablename IN (
      'ordenes', 
      'ejecucion', 
      'datosejecucion', 
      'stock_critico', 
      'pedidos', 
      'cantidad_solicitada', 
      'vencimientos_parques'
  )
ORDER BY tablename;

-- Si no aparecen las 7 tablas, ejecuta el contenido de schema.sql completo
-- O ejecuta este script que crea solo las tablas faltantes:

-- TABLA: ordenes
CREATE TABLE IF NOT EXISTS public.ordenes (
    id SERIAL PRIMARY KEY,
    id_llamado BIGINT NOT NULL,
    llamado TEXT,
    p_unit NUMERIC(18,6),
    fec_contrato VARCHAR(1000),
    oc TEXT,
    item TEXT,
    codigo TEXT,
    producto TEXT,
    cant_oc NUMERIC(18,6),
    monto_oc NUMERIC(18,6),
    monto_recepcion NUMERIC(18,6),
    cant_recep NUMERIC(18,6),
    monto_saldo NUMERIC(18,6),
    dias_de_atraso BIGINT,
    estado TEXT,
    stock TEXT,
    referencia TEXT,
    proveedor TEXT,
    lugar_entrega_oc TEXT,
    fec_ult_recep VARCHAR(1000),
    fecha_recibido_proveedor VARCHAR(1000),
    fecha_oc VARCHAR(1000),
    saldo NUMERIC(18,6),
    plazo_entrega TEXT,
    tipo_vigencia TEXT,
    vigencia TEXT,
    det_recep TEXT,
    fecha_orden DATE,
    fecha_vencimiento DATE,
    observaciones TEXT,
    creado_en TIMESTAMPTZ DEFAULT now(),
    actualizado_en TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ordenes_id_llamado ON public.ordenes(id_llamado);
CREATE INDEX IF NOT EXISTS idx_ordenes_codigo ON public.ordenes(codigo);
CREATE INDEX IF NOT EXISTS idx_ordenes_estado ON public.ordenes(estado);

-- TABLA: ejecucion
CREATE TABLE IF NOT EXISTS public.ejecucion (
    id SERIAL PRIMARY KEY,
    id_llamado INTEGER NOT NULL,
    licitacion VARCHAR(255) NOT NULL,
    proveedor VARCHAR(255),
    codigo VARCHAR(255) NOT NULL,
    medicamento TEXT,
    item TEXT,
    cantidad_maxima NUMERIC(18,2),
    cantidad_emitida NUMERIC(18,2),
    cantidad_recepcionada NUMERIC(18,2),
    cantidad_distribuida NUMERIC(18,2),
    monto_adjudicado NUMERIC(18,2),
    monto_emitido NUMERIC(18,2),
    saldo NUMERIC(18,2),
    porcentaje_emitido NUMERIC(18,2),
    ejecucion_mayor_al_50 VARCHAR(10),
    estado_stock VARCHAR(255),
    estado_contrato VARCHAR(255),
    cantidad_ampliacion NUMERIC(18,2),
    porcentaje_ampliado NUMERIC(18,2),
    porcentaje_ampliacion_emitido NUMERIC(18,2),
    obs TEXT,
    cantidad_ejecutada NUMERIC(18,2) DEFAULT 0,
    precio_unitario NUMERIC(18,4),
    monto_total NUMERIC(18,2),
    fecha_ejecucion DATE,
    observaciones TEXT,
    creado_en TIMESTAMPTZ DEFAULT now(),
    actualizado_en TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ejecucion_id_llamado ON public.ejecucion(id_llamado);
CREATE INDEX IF NOT EXISTS idx_ejecucion_codigo ON public.ejecucion(codigo);
CREATE INDEX IF NOT EXISTS idx_ejecucion_item ON public.ejecucion(item);

-- TABLA: datosejecucion
CREATE TABLE IF NOT EXISTS public.datosejecucion (
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

CREATE INDEX IF NOT EXISTS idx_datosejecucion_vigente ON public.datosejecucion(vigente);

-- TABLA: stock_critico
CREATE TABLE IF NOT EXISTS public.stock_critico (
    id SERIAL PRIMARY KEY,
    codigo TEXT NOT NULL,
    producto TEXT,
    concentracion TEXT,
    forma_farmaceutica TEXT,
    presentacion TEXT,
    clasificacion TEXT,
    meses_en_movimiento INTEGER,
    cantidad_distribuida NUMERIC(18,2),
    stock_actual NUMERIC(18,2),
    stock_reservado NUMERIC(18,2),
    stock_disponible NUMERIC(18,2),
    dmp NUMERIC(18,2),
    estado_stock VARCHAR(50),
    stock_hosp NUMERIC(18,2),
    oc VARCHAR(255),
    descripcion TEXT,
    stock_minimo NUMERIC(18,2) DEFAULT 0,
    estado VARCHAR(50),
    ultima_actualizacion TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_stock_critico_codigo ON public.stock_critico(codigo);
CREATE INDEX IF NOT EXISTS idx_stock_critico_estado ON public.stock_critico(estado);

-- TABLA: pedidos
CREATE TABLE IF NOT EXISTS public.pedidos (
    id SERIAL PRIMARY KEY,
    nro_pedido VARCHAR(255),
    simese VARCHAR(255),
    fecha_pedido DATE,
    codigo VARCHAR(255),
    medicamento TEXT,
    stock NUMERIC(18,2),
    dmp NUMERIC(18,2),
    cantidad NUMERIC(18,2),
    meses_cantidad NUMERIC(18,2),
    dias_transcurridos INTEGER,
    estado VARCHAR(50),
    prioridad VARCHAR(255),
    nro_oc VARCHAR(255),
    fecha_oc DATE,
    opciones VARCHAR(255),
    id_llamado INTEGER,
    item INTEGER,
    cantidad_solicitada NUMERIC(18,2),
    cantidad_pendiente NUMERIC(18,2),
    fecha_solicitud DATE,
    fecha_requerida DATE,
    observaciones TEXT,
    creado_en TIMESTAMPTZ DEFAULT now(),
    actualizado_en TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pedidos_id_llamado ON public.pedidos(id_llamado);
CREATE INDEX IF NOT EXISTS idx_pedidos_codigo ON public.pedidos(codigo);
CREATE INDEX IF NOT EXISTS idx_pedidos_estado ON public.pedidos(estado);

-- TABLA: cantidad_solicitada
CREATE TABLE IF NOT EXISTS public.cantidad_solicitada (
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
    ON public.cantidad_solicitada(emitir_en) 
    WHERE emitir_en IS NOT NULL;

-- TABLA: vencimientos_parques
CREATE TABLE IF NOT EXISTS public.vencimientos_parques (
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

CREATE INDEX IF NOT EXISTS idx_vencimientos_codigo ON public.vencimientos_parques(codigo);
CREATE INDEX IF NOT EXISTS idx_vencimientos_fecha ON public.vencimientos_parques(fec_vencimiento);

-- Verificar nuevamente después de crear
SELECT 
    tablename,
    schemaname,
    '✅ Creada' AS estado
FROM pg_catalog.pg_tables
WHERE schemaname = 'public'
  AND tablename IN (
      'ordenes', 
      'ejecucion', 
      'datosejecucion', 
      'stock_critico', 
      'pedidos', 
      'cantidad_solicitada', 
      'vencimientos_parques'
  )
ORDER BY tablename;
