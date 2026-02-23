-- =============================================================================
-- SICIAP CLOUD - MIGRACIÓN DEFINITIVA
-- Script SQL ÚNICO y ROBUSTO para replicar la lógica exacta de siciap_app.py
-- Ejecutar en Supabase SQL Editor (schema public)
-- =============================================================================

-- =============================================================================
-- PARTE 1: CORRECCIÓN DE TIPOS (Blindaje contra errores de importación)
-- =============================================================================

-- Asegurar que las columnas críticas sean TEXT para tolerar valores mixtos del Excel
DO $$
BEGIN
    -- ejecucion.item
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' 
          AND table_name = 'ejecucion' 
          AND column_name = 'item'
          AND data_type != 'text'
    ) THEN
        ALTER TABLE public.ejecucion ALTER COLUMN item TYPE TEXT USING item::TEXT;
        RAISE NOTICE 'ejecucion.item convertido a TEXT';
    END IF;
    
    -- stock_critico.codigo
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' 
          AND table_name = 'stock_critico' 
          AND column_name = 'codigo'
          AND data_type != 'text'
    ) THEN
        ALTER TABLE public.stock_critico ALTER COLUMN codigo TYPE TEXT USING codigo::TEXT;
        RAISE NOTICE 'stock_critico.codigo convertido a TEXT';
    END IF;
    
    -- ordenes.item
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' 
          AND table_name = 'ordenes' 
          AND column_name = 'item'
          AND data_type != 'text'
    ) THEN
        ALTER TABLE public.ordenes ALTER COLUMN item TYPE TEXT USING item::TEXT;
        RAISE NOTICE 'ordenes.item convertido a TEXT';
    END IF;
    
    -- pedidos.codigo (si existe)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' 
          AND table_name = 'pedidos' 
          AND column_name = 'codigo'
          AND data_type != 'text'
    ) THEN
        ALTER TABLE public.pedidos ALTER COLUMN codigo TYPE TEXT USING codigo::TEXT;
        RAISE NOTICE 'pedidos.codigo convertido a TEXT';
    END IF;
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error en corrección de tipos: %', SQLERRM;
END $$;

-- =============================================================================
-- PARTE 2: TABLAS DE DATOS ANEXOS (Persistencia de Usuario)
-- =============================================================================

-- 2.1 Tabla cantidad_solicitada (PK compuesta: id_llamado, licitacion, codigo, item)
CREATE TABLE IF NOT EXISTS public.cantidad_solicitada (
    id_llamado INTEGER NOT NULL,
    licitacion VARCHAR(255) NOT NULL,
    codigo TEXT NOT NULL,
    item TEXT NOT NULL,
    cantidad_solicitada NUMERIC(18,2) DEFAULT 0,
    emitir_en DATE,
    comentario TEXT,
    actualizado_en TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (id_llamado, licitacion, codigo, item)
);

-- Asegurar que item sea TEXT si la tabla ya existía
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' 
          AND table_name = 'cantidad_solicitada' 
          AND column_name = 'item'
          AND data_type != 'text'
    ) THEN
        ALTER TABLE public.cantidad_solicitada ALTER COLUMN item TYPE TEXT USING item::TEXT;
    END IF;
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;

-- Agregar columnas si no existen
ALTER TABLE public.cantidad_solicitada
  ADD COLUMN IF NOT EXISTS comentario TEXT,
  ADD COLUMN IF NOT EXISTS actualizado_en TIMESTAMPTZ DEFAULT now();

CREATE INDEX IF NOT EXISTS idx_cantidad_solicitada_id_llamado ON public.cantidad_solicitada(id_llamado);
CREATE INDEX IF NOT EXISTS idx_cantidad_solicitada_codigo ON public.cantidad_solicitada(codigo);

COMMENT ON TABLE public.cantidad_solicitada IS 'Cantidad solicitada y Ver en fecha por ítem (editable desde el dashboard)';

-- 2.2 Tabla datosejecucion (PK: id_llamado)
CREATE TABLE IF NOT EXISTS public.datosejecucion (
    id_llamado INTEGER PRIMARY KEY,
    licitacion VARCHAR(255),
    llamado VARCHAR(255),
    descripcion_llamado TEXT,
    vigente TEXT DEFAULT 'SI',  -- TEXT para permitir 'SI', 'NO', 'PENDIENTE DE ADENDA'
    dirigido_a TEXT,
    lugares TEXT,  -- También puede ser lugares_entrega
    fecha_inicio DATE,
    fecha_fin DATE,
    numero_contrato VARCHAR(255),
    monto_total NUMERIC(18,2),
    precio_unitario NUMERIC(18,4),
    observaciones_generales TEXT,
    estado_manual TEXT,
    creado_en TIMESTAMPTZ DEFAULT now(),
    actualizado_en TIMESTAMPTZ DEFAULT now()
);

-- Agregar columnas si no existen
ALTER TABLE public.datosejecucion
  ADD COLUMN IF NOT EXISTS observaciones_generales TEXT,
  ADD COLUMN IF NOT EXISTS estado_manual TEXT,
  ADD COLUMN IF NOT EXISTS lugares TEXT;

-- Si vigente es BOOLEAN, convertirlo a TEXT
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' 
          AND table_name = 'datosejecucion' 
          AND column_name = 'vigente'
          AND data_type = 'boolean'
    ) THEN
        ALTER TABLE public.datosejecucion 
        ALTER COLUMN vigente TYPE TEXT 
        USING CASE WHEN vigente THEN 'SI' ELSE 'NO' END;
        RAISE NOTICE 'datosejecucion.vigente convertido de BOOLEAN a TEXT';
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error al modificar datosejecucion.vigente: %', SQLERRM;
END $$;

CREATE INDEX IF NOT EXISTS idx_datosejecucion_vigente ON public.datosejecucion(vigente);
CREATE INDEX IF NOT EXISTS idx_datosejecucion_id_llamado ON public.datosejecucion(id_llamado);

COMMENT ON TABLE public.datosejecucion IS 'Datos adicionales de ejecución por llamado (vigente, dirigido a, lugares, etc.)';

-- =============================================================================
-- PARTE 3: VISTA MAESTRA vista_tablero_principal (El Cerebro)
-- Replica EXACTAMENTE la lógica de siciap_app.py
-- =============================================================================
-- DROP primero evita el error "cannot change name of view column" al cambiar
-- orden o nombres de columnas respecto a la vista anterior.
DROP VIEW IF EXISTS public.vista_tablero_principal CASCADE;

CREATE VIEW public.vista_tablero_principal AS
WITH
-- Stock por código desde stock_critico
stock_por_codigo AS (
    SELECT
        TRIM(CAST(codigo AS TEXT)) AS codigo,
        COALESCE(stock_disponible, 0) AS stock_disponible,
        COALESCE(stock_actual, 0) AS stock_actual,
        COALESCE(dmp, 0) AS dmp
    FROM public.stock_critico
    WHERE codigo IS NOT NULL AND TRIM(CAST(codigo AS TEXT)) != ''
),
-- Stock sin vencidos desde vencimientos_parques (si existe)
venc_por_codigo AS (
    SELECT
        TRIM(CAST(codigo AS TEXT)) AS codigo,
        SUM(COALESCE(stock_disponible, 0)) AS stock_sin_vencidos
    FROM public.vencimientos_parques
    WHERE codigo IS NOT NULL
      AND (fec_vencimiento >= CURRENT_DATE OR fec_vencimiento IS NULL OR EXTRACT(YEAR FROM fec_vencimiento) = 5000)
    GROUP BY TRIM(CAST(codigo AS TEXT))
),
-- Pendiente de entrega desde órdenes (excl. entregado/finalizado)
pendiente_entrega AS (
    SELECT
        id_llamado,
        COALESCE(TRIM(CAST(llamado AS TEXT)), '') AS licitacion,
        COALESCE(TRIM(CAST(proveedor AS TEXT)), '') AS proveedor,
        TRIM(CAST(codigo AS TEXT)) AS codigo,
        SUM(COALESCE(saldo, 0)) AS pendiente_entrega
    FROM public.ordenes
    WHERE codigo IS NOT NULL AND TRIM(CAST(codigo AS TEXT)) != ''
      AND (estado IS NULL OR LOWER(TRIM(CAST(estado AS TEXT))) NOT IN (
          'entregado', 'finalizado', 'completado', 'completada',
          'entrega parcial', 'entrega total'
      ))
    GROUP BY id_llamado, llamado, proveedor, codigo
),
-- Ejecución deduplicada: mantener solo un registro por (id_llamado, licitacion, codigo, item)
-- Prioriza el registro más reciente (ID más alto)
ejecucion_dedup AS (
    SELECT DISTINCT ON (e.id_llamado, e.licitacion, TRIM(CAST(e.codigo AS TEXT)), TRIM(CAST(e.item AS TEXT)))
        e.*
    FROM public.ejecucion e
    WHERE e.codigo IS NOT NULL AND TRIM(CAST(e.codigo AS TEXT)) != ''
    ORDER BY 
        e.id_llamado, 
        e.licitacion, 
        TRIM(CAST(e.codigo AS TEXT)), 
        TRIM(CAST(e.item AS TEXT)),
        e.id DESC  -- Prioriza el registro más reciente
)
SELECT
    e.id_llamado,
    e.licitacion,
    COALESCE(NULLIF(TRIM(d.descripcion_llamado), ''), e.licitacion) AS nombre_llamado,
    TRIM(CAST(e.codigo AS TEXT)) AS codigo,
    e.medicamento AS producto,
    e.proveedor,
    COALESCE(e.cantidad_maxima, 0) AS cantidad_maxima,
    COALESCE(e.cantidad_emitida, 0) AS cantidad_emitida,
    -- Saldo contrato: cantidad_maxima - cantidad_emitida
    (COALESCE(e.cantidad_maxima, 0) - COALESCE(e.cantidad_emitida, 0)) AS saldo_contrato,
    COALESCE(e.porcentaje_emitido, 0) AS porcentaje_emitido,
    COALESCE(e.precio_unitario, d.precio_unitario) AS precio_unitario,
    e.item,
    COALESCE(d.dirigido_a, '') AS dirigido_a,
    COALESCE(d.lugares, '') AS lugar,
    COALESCE(d.vigente::TEXT, '') AS vigente,
    COALESCE(pe.pendiente_entrega, 0) AS pendiente_entrega,
    -- Stock actual: prioriza stock sin vencidos, luego stock disponible, luego stock_actual
    COALESCE(
        NULLIF(v.stock_sin_vencidos, 0),
        s.stock_disponible,
        s.stock_actual,
        0
    ) AS stock_actual,
    COALESCE(s.dmp, 0) AS dmp_actual,
    -- Cantidad solicitada y fecha
    COALESCE(cs.cantidad_solicitada, 0) AS cantidad_solicitada,
    cs.emitir_en AS ver_en_fecha,
    cs.comentario AS comentario,
    -- COBERTURA EN MESES: (Stock actual + Saldo contrato + Cantidad solicitada) / DMP
    -- Replica EXACTAMENTE la lógica de siciap_app.py: (s + p + c) / d
    CASE
        WHEN COALESCE(s.dmp, 0) > 0 THEN
            ROUND(
                (
                    COALESCE(
                        NULLIF(v.stock_sin_vencidos, 0),
                        s.stock_disponible,
                        s.stock_actual,
                        0
                    ) + 
                    (COALESCE(e.cantidad_maxima, 0) - COALESCE(e.cantidad_emitida, 0)) + 
                    COALESCE(cs.cantidad_solicitada, 0)
                ) / s.dmp,
                1
            )
        ELSE NULL
    END AS cobertura_meses,
    -- NIVEL STOCK (Semáforo): basado en cobertura_meses
    CASE
        WHEN COALESCE(s.dmp, 0) = 0 THEN 'Sin DMP'
        WHEN COALESCE(
            NULLIF(v.stock_sin_vencidos, 0),
            s.stock_disponible,
            s.stock_actual,
            0
        ) = 0 THEN 'Sin Stock'
        WHEN (
            CASE
                WHEN COALESCE(s.dmp, 0) > 0 THEN
                    ROUND(
                        (
                            COALESCE(
                                NULLIF(v.stock_sin_vencidos, 0),
                                s.stock_disponible,
                                s.stock_actual,
                                0
                            ) + 
                            (COALESCE(e.cantidad_maxima, 0) - COALESCE(e.cantidad_emitida, 0)) + 
                            COALESCE(cs.cantidad_solicitada, 0)
                        ) / s.dmp,
                        1
                    )
                ELSE NULL
            END
        ) < 1 THEN 'Crítico'
        WHEN (
            CASE
                WHEN COALESCE(s.dmp, 0) > 0 THEN
                    ROUND(
                        (
                            COALESCE(
                                NULLIF(v.stock_sin_vencidos, 0),
                                s.stock_disponible,
                                s.stock_actual,
                                0
                            ) + 
                            (COALESCE(e.cantidad_maxima, 0) - COALESCE(e.cantidad_emitida, 0)) + 
                            COALESCE(cs.cantidad_solicitada, 0)
                        ) / s.dmp,
                        1
                    )
                ELSE NULL
            END
        ) BETWEEN 1 AND 3 THEN 'Atención'
        ELSE 'Óptimo'
    END AS nivel_stock
FROM ejecucion_dedup e
LEFT JOIN public.datosejecucion d ON e.id_llamado = d.id_llamado
LEFT JOIN pendiente_entrega pe
    ON e.id_llamado = pe.id_llamado
    AND TRIM(CAST(e.licitacion AS TEXT)) = pe.licitacion
    AND TRIM(CAST(e.proveedor AS TEXT)) = pe.proveedor
    AND TRIM(CAST(e.codigo AS TEXT)) = pe.codigo
LEFT JOIN stock_por_codigo s ON TRIM(CAST(e.codigo AS TEXT)) = s.codigo
LEFT JOIN venc_por_codigo v ON TRIM(CAST(e.codigo AS TEXT)) = v.codigo
LEFT JOIN public.cantidad_solicitada cs
    ON e.id_llamado = cs.id_llamado
    AND TRIM(CAST(e.licitacion AS TEXT)) = TRIM(CAST(cs.licitacion AS TEXT))
    AND TRIM(CAST(e.codigo AS TEXT)) = TRIM(CAST(cs.codigo AS TEXT))
    AND TRIM(CAST(e.item AS TEXT)) = TRIM(CAST(cs.item AS TEXT))
WHERE e.codigo IS NOT NULL AND TRIM(CAST(e.codigo AS TEXT)) != ''
ORDER BY e.id_llamado, e.licitacion, e.codigo, e.item;

COMMENT ON VIEW public.vista_tablero_principal IS 'Vista unificada que replica EXACTAMENTE la lógica de siciap_app.py: cobertura_meses = (Stock + Saldo + Cantidad Solicitada) / DMP, nivel_stock basado en cobertura';

-- =============================================================================
-- VERIFICACIÓN FINAL
-- =============================================================================

DO $$
DECLARE
    v_count INTEGER;
BEGIN
    -- Verificar cantidad_solicitada
    SELECT COUNT(*) INTO v_count
    FROM information_schema.columns
    WHERE table_schema = 'public' 
      AND table_name = 'cantidad_solicitada'
      AND column_name = 'item'
      AND data_type = 'text';
    
    IF v_count = 0 THEN
        RAISE NOTICE 'ADVERTENCIA: cantidad_solicitada.item no es TEXT';
    ELSE
        RAISE NOTICE 'OK: cantidad_solicitada.item es TEXT';
    END IF;
    
    -- Verificar datosejecucion
    SELECT COUNT(*) INTO v_count
    FROM information_schema.tables
    WHERE table_schema = 'public' 
      AND table_name = 'datosejecucion';
    
    IF v_count = 0 THEN
        RAISE NOTICE 'ADVERTENCIA: datosejecucion no existe';
    ELSE
        RAISE NOTICE 'OK: datosejecucion existe';
    END IF;
    
    -- Verificar vista
    SELECT COUNT(*) INTO v_count
    FROM information_schema.views
    WHERE table_schema = 'public' 
      AND table_name = 'vista_tablero_principal';
    
    IF v_count = 0 THEN
        RAISE NOTICE 'ADVERTENCIA: vista_tablero_principal no existe';
    ELSE
        RAISE NOTICE 'OK: vista_tablero_principal existe';
    END IF;
    
    RAISE NOTICE '=== MIGRACIÓN COMPLETADA ===';
END $$;

-- =============================================================================
-- FIN DEL SCRIPT
-- =============================================================================
