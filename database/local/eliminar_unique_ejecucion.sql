-- =============================================================================
-- ELIMINAR RESTRICCIÓN UNIQUE DE ejecucion (Base Local)
-- Ejecutar esto en tu PostgreSQL local para permitir duplicados
-- =============================================================================

-- Verificar si existe la restricción
SELECT 
    constraint_name,
    constraint_type
FROM information_schema.table_constraints
WHERE table_schema = 'siciap'
  AND table_name = 'ejecucion'
  AND constraint_type = 'UNIQUE';

-- Eliminar la restricción UNIQUE si existe
ALTER TABLE siciap.ejecucion 
DROP CONSTRAINT IF EXISTS ejecucion_id_llamado_licitacion_codigo_item_key;

-- Verificar que se eliminó
SELECT 
    constraint_name,
    constraint_type
FROM information_schema.table_constraints
WHERE table_schema = 'siciap'
  AND table_name = 'ejecucion'
  AND constraint_type = 'UNIQUE';

-- Debería devolver 0 filas (sin restricciones UNIQUE)
