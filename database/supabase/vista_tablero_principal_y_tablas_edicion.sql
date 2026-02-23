-- =============================================================================
-- SICIAP CLOUD - Tablas de edición manual + Vista tablero principal
-- Para ejecutar en Supabase SQL Editor (schema public)
-- Basado en la lógica de siciap_app._build_vista_unificada_df
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. TABLAS DE EDICIÓN MANUAL (datos que NO se borran al sincronizar)
-- -----------------------------------------------------------------------------

-- 1.1 cantidad_solicitada: ya existe; compatibilidad con item tipo texto y comentario
-- Permitir item como TEXT para valores como "2-2.2" (igual que ejecucion.item)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'cantidad_solicitada' AND column_name = 'item'
          AND data_type = 'integer'
    ) THEN
        ALTER TABLE public.cantidad_solicitada ALTER COLUMN item TYPE TEXT USING item::TEXT;
    END IF;
EXCEPTION WHEN OTHERS THEN
    NULL; -- Si falla (ej. por restricción PK), ignorar
END $$;

ALTER TABLE public.cantidad_solicitada
  ADD COLUMN IF NOT EXISTS comentario TEXT;

COMMENT ON TABLE public.cantidad_solicitada IS 'Cantidad solicitada y Ver en fecha por ítem (editable desde el dashboard)';

-- 1.2 datosejecucion: agregar columnas de edición manual si no existen
ALTER TABLE public.datosejecucion
  ADD COLUMN IF NOT EXISTS observaciones_generales TEXT,
  ADD COLUMN IF NOT EXISTS estado_manual TEXT;

-- lugares ya existe; si en el prompt era lugares_entrega, es el mismo concepto
COMMENT ON COLUMN public.datosejecucion.lugares IS 'Lugares de entrega (editable)';

-- 1.3 recordatorios: tabla para alertas de fecha
CREATE TABLE IF NOT EXISTS public.recordatorios (
    id SERIAL PRIMARY KEY,
    id_llamado INTEGER,
    licitacion VARCHAR(255),
    codigo VARCHAR(255),
    item TEXT,
    mensaje TEXT,
    fecha_alerta DATE NOT NULL,
    resuelto BOOLEAN DEFAULT FALSE,
    creado_en TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_recordatorios_fecha_alerta ON public.recordatorios(fecha_alerta);
CREATE INDEX IF NOT EXISTS idx_recordatorios_resuelto ON public.recordatorios(resuelto);

COMMENT ON TABLE public.recordatorios IS 'Recordatorios y alertas por ítem';

-- -----------------------------------------------------------------------------
-- 2. VISTA MAESTRA: vista_tablero_principal
-- Replica el cruce de _build_vista_unificada_df (ejecucion + datosejecucion +
-- órdenes pendientes + stock_critico + vencimientos + cantidad_solicitada)
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW public.vista_tablero_principal AS
WITH
-- Stock por código desde stock_critico
stock_por_codigo AS (
    SELECT
        TRIM(CAST(codigo AS TEXT)) AS codigo,
        COALESCE(stock_disponible, 0) AS stock_disponible,
        COALESCE(dmp, 0) AS dmp
    FROM public.stock_critico
    WHERE codigo IS NOT NULL AND TRIM(CAST(codigo AS TEXT)) != ''
),
-- Stock sin vencidos desde vencimientos_parques
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
    (COALESCE(e.cantidad_maxima, 0) - COALESCE(e.cantidad_emitida, 0)) AS saldo_contrato,
    COALESCE(e.porcentaje_emitido, 0) AS porcentaje_emitido,
    COALESCE(e.precio_unitario, d.precio_unitario) AS precio_unitario,
    e.item,
    COALESCE(d.dirigido_a, '') AS dirigido_a,
    COALESCE(d.lugares, '') AS lugar,
    COALESCE(d.vigente::TEXT, '') AS vigente,
    COALESCE(pe.pendiente_entrega, 0) AS pendiente_entrega,
    COALESCE(
        NULLIF(v.stock_sin_vencidos, 0),
        s.stock_disponible,
        0
    ) AS stock_actual,
    COALESCE(s.dmp, 0) AS dmp_actual,
    CASE
        WHEN COALESCE(s.dmp, 0) = 0 THEN 'Sin DMP'
        WHEN COALESCE(
            NULLIF(v.stock_sin_vencidos, 0),
            s.stock_disponible,
            0
        ) = 0 THEN 'Sin Stock'
        WHEN COALESCE(
            NULLIF(v.stock_sin_vencidos, 0),
            s.stock_disponible,
            0
        ) < s.dmp * 0.3 THEN 'Crítico'
        WHEN COALESCE(
            NULLIF(v.stock_sin_vencidos, 0),
            s.stock_disponible,
            0
        ) < s.dmp * 0.7 THEN 'Atención'
        ELSE 'Óptimo'
    END AS nivel_stock,
    COALESCE(cs.cantidad_solicitada, 0) AS cantidad_solicitada,
    cs.emitir_en AS ver_en_fecha,
    cs.comentario AS comentario,
    CASE
        WHEN COALESCE(s.dmp, 0) > 0 THEN
            ((COALESCE(e.cantidad_maxima, 0) - COALESCE(e.cantidad_emitida, 0)) + COALESCE(cs.cantidad_solicitada, 0)) / s.dmp
        ELSE NULL
    END AS cobertura_meses
FROM public.ejecucion e
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

COMMENT ON VIEW public.vista_tablero_principal IS 'Vista unificada para el dashboard editable (ejecución + stock + cantidad solicitada + cobertura)';
