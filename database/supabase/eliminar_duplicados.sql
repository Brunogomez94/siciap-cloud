-- =============================================================================
-- SCRIPT PARA ELIMINAR DUPLICADOS DE LAS TABLAS
-- Ejecutar en Supabase SQL Editor después de cargar datos desde Excel
-- =============================================================================

-- Eliminar duplicados de ejecucion
-- Mantiene solo un registro por (id_llamado, licitacion, codigo, item)
-- Prioriza el registro más reciente (ID más alto)
DELETE FROM public.ejecucion
WHERE id IN (
    SELECT id
    FROM (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY id_llamado, licitacion, TRIM(CAST(codigo AS TEXT)), TRIM(CAST(item AS TEXT))
                   ORDER BY id DESC
               ) AS rn
        FROM public.ejecucion
        WHERE codigo IS NOT NULL AND TRIM(CAST(codigo AS TEXT)) != ''
    ) t
    WHERE rn > 1
);

-- Eliminar duplicados de ordenes
-- Mantiene solo un registro por (id_llamado, llamado, codigo, item, oc)
-- Prioriza el registro más reciente (ID más alto)
DELETE FROM public.ordenes
WHERE id IN (
    SELECT id
    FROM (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY id_llamado, llamado, TRIM(CAST(codigo AS TEXT)), TRIM(CAST(item AS TEXT)), oc
                   ORDER BY id DESC
               ) AS rn
        FROM public.ordenes
        WHERE codigo IS NOT NULL AND TRIM(CAST(codigo AS TEXT)) != ''
    ) t
    WHERE rn > 1
);

-- Verificar resultados
SELECT 
    'ejecucion' AS tabla,
    COUNT(*) AS total_registros,
    COUNT(DISTINCT (id_llamado, licitacion, TRIM(CAST(codigo AS TEXT)), TRIM(CAST(item AS TEXT)))) AS registros_unicos
FROM public.ejecucion
WHERE codigo IS NOT NULL AND TRIM(CAST(codigo AS TEXT)) != ''

UNION ALL

SELECT 
    'ordenes' AS tabla,
    COUNT(*) AS total_registros,
    COUNT(DISTINCT (id_llamado, llamado, TRIM(CAST(codigo AS TEXT)), TRIM(CAST(item AS TEXT)), oc)) AS registros_unicos
FROM public.ordenes
WHERE codigo IS NOT NULL AND TRIM(CAST(codigo AS TEXT)) != '';
